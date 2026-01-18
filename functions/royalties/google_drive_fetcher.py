import io
from typing import List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from .models import DriveFile


class GoogleDriveFetcher:
    """
    Fetches .xlsx files from a Google Drive folder.

    Authentication options:
    1. Service account JSON key file (for local development)
    2. Default credentials (for Cloud Functions with attached service account)

    Usage:
        # With explicit credentials file
        fetcher = GoogleDriveFetcher(
            folder_id="your-folder-id",
            credentials_path="/path/to/service-account.json"
        )

        # With default credentials (in Cloud Functions)
        fetcher = GoogleDriveFetcher(folder_id="your-folder-id")

        # List xlsx files
        files = fetcher.list_xlsx_files()

        # Download a file
        content = fetcher.download_file(files[0].id)
    """

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    def __init__(
        self,
        folder_id: str,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize the Google Drive fetcher.

        Args:
            folder_id: The ID of the Google Drive folder to fetch from.
                       (Found in the folder URL after /folders/)
            credentials_path: Path to service account JSON key file.
                              If None, uses Application Default Credentials.
        """
        self.folder_id = folder_id
        self._service = self._build_service(credentials_path)
        self._verify_folder_access()

    def _verify_folder_access(self) -> None:
        """Verify that we have access to the configured folder."""
        try:
            folder = (
                self._service.files()
                .get(fileId=self.folder_id, fields="id, name, mimeType")
                .execute()
            )
            # Verify it's actually a folder
            if folder.get("mimeType") != "application/vnd.google-apps.folder":
                raise ValueError(
                    f"ID '{self.folder_id}' is not a folder "
                    f"(mimeType: {folder.get('mimeType')})"
                )
        except HttpError as e:
            if e.resp.status == 404:
                raise PermissionError(
                    f"Cannot access folder '{self.folder_id}'. "
                    "Either the folder does not exist or the service account "
                    "does not have permission to access it. "
                    "Make sure the folder is shared with the service account email."
                ) from e
            raise

    def _build_service(self, credentials_path: Optional[str]):
        """Build the Google Drive API service."""
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=self.SCOPES
            )
        else:
            # Use Application Default Credentials (works in Cloud Functions)
            from google.auth import default

            credentials, _ = default(scopes=self.SCOPES)

        return build("drive", "v3", credentials=credentials)

    def list_xlsx_files(self) -> List[DriveFile]:
        """
        List all .xlsx files in the configured folder.

        Returns:
            List of DriveFile objects representing xlsx files in the folder.
        """
        query = (
            f"'{self.folder_id}' in parents "
            "and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' "
            "and trashed=false"
        )

        files = []
        page_token = None

        while True:
            response = (
                self._service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken=page_token,
                )
                .execute()
            )

            for file in response.get("files", []):
                files.append(DriveFile(id=file["id"], name=file["name"]))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return files

    def download_file(self, file_id: str) -> bytes:
        """
        Download a file's content.

        Args:
            file_id: The Google Drive file ID.

        Returns:
            The file content as bytes.
        """
        request = self._service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        buffer.seek(0)
        return buffer.read()
