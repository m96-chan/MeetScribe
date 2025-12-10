"""
Google Docs OUTPUT renderer for MeetScribe.

Creates Google Docs with formatted meeting minutes using Google Docs API.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.models import Minutes
from ..core.providers import OutputRenderer

logger = logging.getLogger(__name__)


class GoogleDocsRenderer(OutputRenderer):
    """
    Google Docs OUTPUT renderer.

    Creates professionally formatted Google Docs meeting minutes.
    """

    # API scopes required
    SCOPES = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google Docs renderer.

        Config params:
            credentials_path: Path to OAuth credentials JSON
            service_account_path: Path to service account JSON
            token_path: Path to store OAuth token
            folder_id: Google Drive folder ID for documents
            share_with: List of emails to share with
            document_title_template: Template for doc title
        """
        super().__init__(config)

        self.credentials_path = config.get("credentials_path") or os.getenv(
            "GOOGLE_CREDENTIALS_PATH"
        )
        self.service_account_path = config.get("service_account_path") or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_PATH"
        )
        self.token_path = config.get("token_path", "./token.json")
        self.folder_id = config.get("folder_id")
        self.share_with = config.get("share_with", [])
        self.document_title_template = config.get(
            "document_title_template", "Meeting Minutes: {meeting_id}"
        )

        # Output dir for local backup
        self.output_dir = Path(config.get("output_dir", "./meetings"))

        # Initialize API client
        self.docs_service = None
        self.drive_service = None
        self._init_services()

    def _init_services(self):
        """Initialize Google API services."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None

            # Try service account first
            if self.service_account_path and Path(self.service_account_path).exists():
                creds = service_account.Credentials.from_service_account_file(
                    self.service_account_path, scopes=self.SCOPES
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
                    with open(token_path, "w") as f:
                        f.write(creds.to_json())

                logger.info("Using OAuth credentials")

            if creds:
                self.docs_service = build("docs", "v1", credentials=creds)
                self.drive_service = build("drive", "v3", credentials=creds)
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
        Render minutes to Google Docs.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            URL to Google Doc
        """
        logger.info(f"Rendering Google Docs output for {meeting_id}")

        if self.docs_service:
            doc_url = self._create_google_doc(minutes, meeting_id)
        else:
            doc_url = self._create_mock_output(minutes, meeting_id)

        logger.info(f"Google Doc created: {doc_url}")
        return doc_url

    def _create_google_doc(self, minutes: Minutes, meeting_id: str) -> str:
        """Create actual Google Doc."""
        # Create document
        title = self.document_title_template.format(meeting_id=meeting_id)
        doc = self.docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        # Build document content
        requests = self._build_document_requests(minutes, meeting_id)

        # Update document
        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()

        # Move to folder if specified
        if self.folder_id:
            self._move_to_folder(doc_id, self.folder_id)

        # Share with users
        for email in self.share_with:
            self._share_document(doc_id, email)

        # Save local backup
        self._save_local_backup(minutes, meeting_id, doc_url)

        return doc_url

    def _build_document_requests(self, minutes: Minutes, meeting_id: str) -> List[Dict]:
        """Build Google Docs API requests."""
        requests = []
        index = 1  # Document starts at index 1

        # Helper to add text
        def add_text(text: str, style: Optional[Dict] = None) -> int:
            nonlocal index
            requests.append({"insertText": {"location": {"index": index}, "text": text}})
            start = index
            index += len(text)

            if style:
                requests.append(
                    {
                        "updateParagraphStyle": {
                            "range": {"startIndex": start, "endIndex": index},
                            "paragraphStyle": style,
                            "fields": ",".join(style.keys()),
                        }
                    }
                )

            return index

        def add_heading(text: str, level: int = 1):
            add_text(text + "\n", {"namedStyleType": f"HEADING_{level}"})

        def add_body(text: str):
            add_text(text + "\n", {"namedStyleType": "NORMAL_TEXT"})

        # Title
        add_heading(f"Meeting Minutes: {meeting_id}", 1)

        # Metadata
        add_body(f"Generated: {minutes.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        add_text("\n")

        # Summary
        add_heading("Summary", 2)
        add_body(minutes.summary)
        add_text("\n")

        # Key Points
        if minutes.key_points:
            add_heading("Key Points", 2)
            for point in minutes.key_points:
                add_body(f"• {point}")
            add_text("\n")

        # Participants
        if minutes.participants:
            add_heading("Participants", 2)
            add_body(", ".join(minutes.participants))
            add_text("\n")

        # Decisions
        if minutes.decisions:
            add_heading("Decisions", 2)
            for i, decision in enumerate(minutes.decisions, 1):
                text = f"{i}. {decision.description}"
                if decision.responsible:
                    text += f" (Responsible: {decision.responsible})"
                if decision.deadline:
                    text += f" (Deadline: {decision.deadline})"
                add_body(text)
            add_text("\n")

        # Action Items
        if minutes.action_items:
            add_heading("Action Items", 2)
            for i, item in enumerate(minutes.action_items, 1):
                text = f"{i}. {item.description}"
                if item.assignee:
                    text += f" - {item.assignee}"
                if item.deadline:
                    text += f" (Due: {item.deadline})"
                if item.priority:
                    text += f" [{item.priority}]"
                add_body(text)
            add_text("\n")

        # Footer
        add_body("---")
        add_body("Generated by MeetScribe")
        if minutes.url:
            add_body(f"NotebookLM: {minutes.url}")

        return requests

    def _move_to_folder(self, doc_id: str, folder_id: str):
        """Move document to specified folder."""
        try:
            # Get current parents
            file = self.drive_service.files().get(fileId=doc_id, fields="parents").execute()
            previous_parents = ",".join(file.get("parents", []))

            # Move to new folder
            self.drive_service.files().update(
                fileId=doc_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields="id, parents",
            ).execute()

            logger.info(f"Moved document to folder: {folder_id}")
        except Exception as e:
            logger.warning(f"Could not move document to folder: {e}")

    def _share_document(self, doc_id: str, email: str):
        """Share document with user."""
        try:
            self.drive_service.permissions().create(
                fileId=doc_id,
                body={"type": "user", "role": "writer", "emailAddress": email},
                sendNotificationEmail=True,
            ).execute()

            logger.info(f"Shared document with: {email}")
        except Exception as e:
            logger.warning(f"Could not share document with {email}: {e}")

    def _save_local_backup(self, minutes: Minutes, meeting_id: str, doc_url: str):
        """Save local backup of document info."""
        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        backup_data = {
            "meeting_id": meeting_id,
            "google_doc_url": doc_url,
            "generated_at": minutes.generated_at.isoformat(),
            "summary": minutes.summary,
        }

        backup_path = meeting_dir / "google_doc_info.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2)

    def _create_mock_output(self, minutes: Minutes, meeting_id: str) -> str:
        """Create mock output when API not available."""
        logger.info(f"[MOCK] Creating Google Doc for {meeting_id}")

        # Save local file
        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        mock_url = f"https://docs.google.com/document/d/mock_{meeting_id}/edit"

        backup_data = {
            "meeting_id": meeting_id,
            "google_doc_url": mock_url,
            "generated_at": minutes.generated_at.isoformat(),
            "summary": minutes.summary,
            "note": "Mock mode - no actual Google Doc created",
        }

        backup_path = meeting_dir / "google_doc_info.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2)

        return mock_url

    def validate_config(self) -> bool:
        """Validate renderer configuration."""
        if not self.credentials_path and not self.service_account_path:
            logger.warning("No Google credentials configured - running in mock mode")
        return True
