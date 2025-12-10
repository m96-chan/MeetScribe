"""
Google Meet Drive INPUT provider for MeetScribe.

Downloads Google Meet recordings from Google Drive.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import json

from ..core.providers import InputProvider


logger = logging.getLogger(__name__)


class GoogleMeetProvider(InputProvider):
    """
    Google Meet Drive INPUT provider.

    Downloads meeting recordings stored in Google Drive.
    """

    # API scopes required
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
    ]

    # Google Meet recording folder name pattern
    MEET_FOLDER_PATTERN = "Meet Recordings"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google Meet provider.

        Config params:
            credentials_path: Path to OAuth credentials JSON
            service_account_path: Path to service account JSON
            token_path: Path to store OAuth token
            folder_id: Specific Drive folder ID to search
            meeting_code: Google Meet meeting code to find
            date_filter: Date filter for recordings (YYYY-MM-DD)
            download_dir: Local directory for downloads
            keep_downloaded: Keep downloaded files (default: True)
        """
        super().__init__(config)

        self.credentials_path = config.get('credentials_path') or os.getenv('GOOGLE_CREDENTIALS_PATH')
        self.service_account_path = config.get('service_account_path') or os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH')
        self.token_path = config.get('token_path', './token.json')
        self.folder_id = config.get('folder_id')
        self.meeting_code = config.get('meeting_code')
        self.date_filter = config.get('date_filter')
        self.download_dir = Path(config.get('download_dir', './downloads'))
        self.keep_downloaded = config.get('keep_downloaded', True)

        # Initialize API client
        self.drive_service = None
        self._init_service()

    def _init_service(self):
        """Initialize Google Drive API service."""
        try:
            from google.oauth2 import service_account
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = None

            # Try service account first
            if self.service_account_path and Path(self.service_account_path).exists():
                creds = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=self.SCOPES
                )
                logger.info("Using service account credentials")

            # Try OAuth credentials
            elif self.credentials_path:
                token_path = Path(self.token_path)

                if token_path.exists():
                    creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)

                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    elif Path(self.credentials_path).exists():
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, self.SCOPES
                        )
                        creds = flow.run_local_server(port=0)

                    # Save token
                    token_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(token_path, 'w') as f:
                        f.write(creds.to_json())

                logger.info("Using OAuth credentials")

            if creds:
                self.drive_service = build('drive', 'v3', credentials=creds)
                logger.info("Google Drive API service initialized")
            else:
                logger.warning("No credentials found - running in mock mode")

        except ImportError:
            logger.warning(
                "Google API packages not installed. Run:\n"
                "pip install google-auth google-auth-oauthlib google-api-python-client\n"
                "Running in mock mode."
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            logger.warning("Running in mock mode")

    def record(self, meeting_id: str) -> Path:
        """
        Download meeting recording from Google Drive.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to downloaded audio file
        """
        logger.info(f"Fetching Google Meet recording for {meeting_id}")

        if self.drive_service:
            audio_path = self._download_recording(meeting_id)
        else:
            audio_path = self._create_mock_file(meeting_id)

        logger.info(f"Recording available at: {audio_path}")
        return audio_path

    def _download_recording(self, meeting_id: str) -> Path:
        """Download actual recording from Drive."""
        from googleapiclient.http import MediaIoBaseDownload
        import io

        # Find recording file
        file_info = self._find_recording()
        if not file_info:
            raise FileNotFoundError(
                f"No Google Meet recording found"
                f"{' for meeting code: ' + self.meeting_code if self.meeting_code else ''}"
            )

        file_id = file_info['id']
        file_name = file_info['name']
        logger.info(f"Found recording: {file_name}")

        # Create download directory
        download_path = self.download_dir / meeting_id
        download_path.mkdir(parents=True, exist_ok=True)

        # Determine output filename
        output_file = download_path / file_name

        # Download file
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                logger.info(f"Download progress: {int(status.progress() * 100)}%")

        # Write to file
        fh.seek(0)
        with open(output_file, 'wb') as f:
            f.write(fh.read())

        logger.info(f"Downloaded: {output_file}")

        # Save metadata
        self._save_metadata(download_path, file_info)

        return output_file

    def _find_recording(self) -> Optional[Dict[str, Any]]:
        """Find recording file in Drive."""
        # Build query
        query_parts = ["mimeType contains 'video/' or mimeType contains 'audio/'"]

        if self.folder_id:
            query_parts.append(f"'{self.folder_id}' in parents")

        if self.meeting_code:
            query_parts.append(f"name contains '{self.meeting_code}'")

        if self.date_filter:
            query_parts.append(f"createdTime >= '{self.date_filter}T00:00:00'")
            query_parts.append(f"createdTime < '{self.date_filter}T23:59:59'")

        query = " and ".join(query_parts)

        # Execute search
        results = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, createdTime, size)',
            orderBy='createdTime desc',
            pageSize=10
        ).execute()

        files = results.get('files', [])

        if not files:
            # Try searching in Meet Recordings folder
            folder_id = self._find_meet_folder()
            if folder_id:
                query_parts = [
                    "mimeType contains 'video/' or mimeType contains 'audio/'",
                    f"'{folder_id}' in parents"
                ]
                if self.meeting_code:
                    query_parts.append(f"name contains '{self.meeting_code}'")

                query = " and ".join(query_parts)
                results = self.drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name, mimeType, createdTime, size)',
                    orderBy='createdTime desc',
                    pageSize=10
                ).execute()
                files = results.get('files', [])

        return files[0] if files else None

    def _find_meet_folder(self) -> Optional[str]:
        """Find Meet Recordings folder."""
        query = f"name = '{self.MEET_FOLDER_PATTERN}' and mimeType = 'application/vnd.google-apps.folder'"

        results = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        folders = results.get('files', [])
        return folders[0]['id'] if folders else None

    def _save_metadata(self, download_path: Path, file_info: Dict[str, Any]):
        """Save recording metadata."""
        metadata = {
            'source': 'google_meet',
            'file_id': file_info['id'],
            'file_name': file_info['name'],
            'mime_type': file_info.get('mimeType'),
            'created_time': file_info.get('createdTime'),
            'size': file_info.get('size'),
            'meeting_code': self.meeting_code,
            'downloaded_at': datetime.now().isoformat()
        }

        meta_path = download_path / 'drive_metadata.json'
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def _create_mock_file(self, meeting_id: str) -> Path:
        """Create mock file when API not available."""
        logger.info(f"[MOCK] Creating mock Google Meet recording for {meeting_id}")

        download_path = self.download_dir / meeting_id
        download_path.mkdir(parents=True, exist_ok=True)

        mock_file = download_path / f"mock_meet_recording_{meeting_id}.txt"
        with open(mock_file, 'w') as f:
            f.write(f"Mock Google Meet recording for {meeting_id}\n")
            f.write("This is a placeholder file for testing.\n")
            f.write("Configure Google Drive API credentials to download actual recordings.\n")

        # Save mock metadata
        metadata = {
            'source': 'google_meet',
            'mock': True,
            'meeting_id': meeting_id,
            'note': 'No actual recording - running in mock mode'
        }

        meta_path = download_path / 'drive_metadata.json'
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        return mock_file

    def list_recordings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List available recordings in Drive.

        Args:
            limit: Maximum number of recordings to return

        Returns:
            List of recording file info dictionaries
        """
        if not self.drive_service:
            logger.warning("Drive service not available")
            return []

        # Find Meet Recordings folder
        folder_id = self.folder_id or self._find_meet_folder()
        if not folder_id:
            logger.warning("Meet Recordings folder not found")
            return []

        query = (
            f"'{folder_id}' in parents and "
            "(mimeType contains 'video/' or mimeType contains 'audio/')"
        )

        results = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, createdTime, size)',
            orderBy='createdTime desc',
            pageSize=limit
        ).execute()

        return results.get('files', [])

    def validate_config(self) -> bool:
        """Validate provider configuration."""
        if not self.credentials_path and not self.service_account_path:
            logger.warning("No Google credentials configured - running in mock mode")
        return True
