"""
Google Spreadsheet OUTPUT renderer for MeetScribe.

Creates Google Spreadsheets with structured meeting data using Google Sheets API.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os
import json

from ..core.providers import OutputRenderer
from ..core.models import Minutes


logger = logging.getLogger(__name__)


class GoogleSheetsRenderer(OutputRenderer):
    """
    Google Sheets OUTPUT renderer.

    Creates structured Google Spreadsheets for action item tracking.
    """

    # API scopes required
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google Sheets renderer.

        Config params:
            credentials_path: Path to OAuth credentials JSON
            service_account_path: Path to service account JSON
            token_path: Path to store OAuth token
            folder_id: Google Drive folder ID for spreadsheets
            share_with: List of emails to share with
            spreadsheet_title_template: Template for spreadsheet title
            existing_spreadsheet_id: ID to append to existing spreadsheet
        """
        super().__init__(config)

        self.credentials_path = config.get('credentials_path') or os.getenv('GOOGLE_CREDENTIALS_PATH')
        self.service_account_path = config.get('service_account_path') or os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH')
        self.token_path = config.get('token_path', './token.json')
        self.folder_id = config.get('folder_id')
        self.share_with = config.get('share_with', [])
        self.spreadsheet_title_template = config.get(
            'spreadsheet_title_template',
            'Meeting Tracker: {meeting_id}'
        )
        self.existing_spreadsheet_id = config.get('existing_spreadsheet_id')

        # Output dir for local backup
        self.output_dir = Path(config.get('output_dir', './meetings'))

        # Initialize API client
        self.sheets_service = None
        self.drive_service = None
        self._init_services()

    def _init_services(self):
        """Initialize Google API services."""
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
                self.sheets_service = build('sheets', 'v4', credentials=creds)
                self.drive_service = build('drive', 'v3', credentials=creds)
                logger.info("Google API services initialized")
            else:
                logger.warning("No credentials found - running in mock mode")

        except ImportError:
            logger.warning(
                "Google API packages not installed. Run:\n"
                "pip install google-auth google-auth-oauthlib google-api-python-client\n"
                "Running in mock mode."
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {e}")
            logger.warning("Running in mock mode")

    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        Render minutes to Google Spreadsheet.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            URL to Google Spreadsheet
        """
        logger.info(f"Rendering Google Sheets output for {meeting_id}")

        if self.sheets_service:
            if self.existing_spreadsheet_id:
                sheet_url = self._append_to_spreadsheet(minutes, meeting_id)
            else:
                sheet_url = self._create_spreadsheet(minutes, meeting_id)
        else:
            sheet_url = self._create_mock_output(minutes, meeting_id)

        logger.info(f"Google Spreadsheet created: {sheet_url}")
        return sheet_url

    def _create_spreadsheet(self, minutes: Minutes, meeting_id: str) -> str:
        """Create new Google Spreadsheet."""
        title = self.spreadsheet_title_template.format(meeting_id=meeting_id)

        # Create spreadsheet
        spreadsheet = {
            'properties': {'title': title},
            'sheets': [
                {'properties': {'title': 'Summary'}},
                {'properties': {'title': 'Action Items'}},
                {'properties': {'title': 'Decisions'}},
            ]
        }

        result = self.sheets_service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = result['spreadsheetId']
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

        # Populate sheets
        self._populate_summary_sheet(spreadsheet_id, minutes, meeting_id)
        self._populate_action_items_sheet(spreadsheet_id, minutes)
        self._populate_decisions_sheet(spreadsheet_id, minutes)

        # Format sheets
        self._format_spreadsheet(spreadsheet_id)

        # Move to folder if specified
        if self.folder_id:
            self._move_to_folder(spreadsheet_id, self.folder_id)

        # Share with users
        for email in self.share_with:
            self._share_spreadsheet(spreadsheet_id, email)

        # Save local backup
        self._save_local_backup(minutes, meeting_id, sheet_url)

        return sheet_url

    def _append_to_spreadsheet(self, minutes: Minutes, meeting_id: str) -> str:
        """Append to existing spreadsheet."""
        spreadsheet_id = self.existing_spreadsheet_id
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

        # Append action items
        if minutes.action_items:
            values = []
            for item in minutes.action_items:
                values.append([
                    meeting_id,
                    minutes.generated_at.strftime('%Y-%m-%d'),
                    item.description,
                    item.assignee or '',
                    item.deadline or '',
                    item.priority or '',
                    'Open'
                ])

            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Action Items!A:G',
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()

        logger.info(f"Appended {len(minutes.action_items)} action items to spreadsheet")
        return sheet_url

    def _populate_summary_sheet(self, spreadsheet_id: str, minutes: Minutes, meeting_id: str):
        """Populate summary sheet."""
        values = [
            ['Meeting Summary'],
            [''],
            ['Meeting ID', meeting_id],
            ['Generated', minutes.generated_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['Participants', ', '.join(minutes.participants) if minutes.participants else 'N/A'],
            [''],
            ['Summary'],
            [minutes.summary],
            [''],
            ['Key Points'],
        ]

        for point in minutes.key_points:
            values.append([f'• {point}'])

        if minutes.url:
            values.extend([
                [''],
                ['NotebookLM URL', minutes.url]
            ])

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Summary!A1',
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()

    def _populate_action_items_sheet(self, spreadsheet_id: str, minutes: Minutes):
        """Populate action items sheet."""
        values = [
            ['#', 'Description', 'Assignee', 'Deadline', 'Priority', 'Status']
        ]

        for i, item in enumerate(minutes.action_items, 1):
            values.append([
                i,
                item.description,
                item.assignee or '',
                item.deadline or '',
                item.priority or '',
                'Open'
            ])

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Action Items!A1',
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()

    def _populate_decisions_sheet(self, spreadsheet_id: str, minutes: Minutes):
        """Populate decisions sheet."""
        values = [
            ['#', 'Decision', 'Responsible', 'Deadline']
        ]

        for i, decision in enumerate(minutes.decisions, 1):
            values.append([
                i,
                decision.description,
                decision.responsible or '',
                decision.deadline or ''
            ])

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Decisions!A1',
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()

    def _format_spreadsheet(self, spreadsheet_id: str):
        """Format spreadsheet with styles."""
        requests = [
            # Format Summary header
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True, 'fontSize': 14}
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat'
                }
            },
            # Format Action Items header
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 1,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            },
            # Format Decisions header
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 2,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            },
            # Auto-resize columns
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 1,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 6
                    }
                }
            },
        ]

        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

    def _move_to_folder(self, spreadsheet_id: str, folder_id: str):
        """Move spreadsheet to specified folder."""
        try:
            file = self.drive_service.files().get(
                fileId=spreadsheet_id,
                fields='parents'
            ).execute()
            previous_parents = ",".join(file.get('parents', []))

            self.drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

            logger.info(f"Moved spreadsheet to folder: {folder_id}")
        except Exception as e:
            logger.warning(f"Could not move spreadsheet to folder: {e}")

    def _share_spreadsheet(self, spreadsheet_id: str, email: str):
        """Share spreadsheet with user."""
        try:
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body={
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': email
                },
                sendNotificationEmail=True
            ).execute()

            logger.info(f"Shared spreadsheet with: {email}")
        except Exception as e:
            logger.warning(f"Could not share spreadsheet with {email}: {e}")

    def _save_local_backup(self, minutes: Minutes, meeting_id: str, sheet_url: str):
        """Save local backup of spreadsheet info."""
        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        backup_data = {
            'meeting_id': meeting_id,
            'google_sheet_url': sheet_url,
            'generated_at': minutes.generated_at.isoformat(),
            'action_items_count': len(minutes.action_items),
            'decisions_count': len(minutes.decisions),
        }

        backup_path = meeting_dir / 'google_sheet_info.json'
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)

    def _create_mock_output(self, minutes: Minutes, meeting_id: str) -> str:
        """Create mock output when API not available."""
        logger.info(f"[MOCK] Creating Google Spreadsheet for {meeting_id}")

        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        mock_url = f"https://docs.google.com/spreadsheets/d/mock_{meeting_id}/edit"

        backup_data = {
            'meeting_id': meeting_id,
            'google_sheet_url': mock_url,
            'generated_at': minutes.generated_at.isoformat(),
            'action_items_count': len(minutes.action_items),
            'decisions_count': len(minutes.decisions),
            'note': 'Mock mode - no actual Google Spreadsheet created'
        }

        backup_path = meeting_dir / 'google_sheet_info.json'
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)

        return mock_url

    def validate_config(self) -> bool:
        """Validate renderer configuration."""
        if not self.credentials_path and not self.service_account_path:
            logger.warning("No Google credentials configured - running in mock mode")
        return True
