import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class FileStorageService:
    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = storage_dir
        self.tickets_file = os.path.join(storage_dir, "tickets.json")
        self._ensure_storage_dir()
        self._load_tickets()

    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_dir, exist_ok=True)
        if not os.path.exists(self.tickets_file):
            self._save_tickets({})

    def _load_tickets(self):
        """Load tickets from the JSON file."""
        try:
            with open(self.tickets_file, 'r') as f:
                self.tickets = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.tickets = {}
            self._save_tickets(self.tickets)

    def _save_tickets(self, tickets: Dict[str, Any]):
        """Save tickets to the JSON file."""
        with open(self.tickets_file, 'w') as f:
            json.dump(tickets, f, default=str, indent=2)

    def save_ticket(self, ticket_id: str, ticket_data: Dict[str, Any]):
        """Save a ticket to storage."""
        self.tickets[ticket_id] = ticket_data
        self._save_tickets(self.tickets)

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get a ticket from storage."""
        return self.tickets.get(ticket_id)

    def update_ticket(self, ticket_id: str, ticket_data: Dict[str, Any]):
        """Update an existing ticket."""
        if ticket_id in self.tickets:
            self.tickets[ticket_id].update(ticket_data)
            self.tickets[ticket_id]['updated_at'] = datetime.utcnow().isoformat()
            self._save_tickets(self.tickets)
            return True
        return False

    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket from storage."""
        if ticket_id in self.tickets:
            del self.tickets[ticket_id]
            self._save_tickets(self.tickets)
            return True
        return False

    def get_all_tickets(self) -> Dict[str, Any]:
        """Get all tickets."""
        return self.tickets

class StorageService:
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        """Ensure the blob container exists"""
        try:
            self.blob_service_client.create_container(self.container_name)
            logger.info(f"Container {self.container_name} created successfully")
        except ResourceExistsError:
            logger.info(f"Container {self.container_name} already exists")

    async def upload_file(self, file_path: str, blob_name: Optional[str] = None) -> str:
        """
        Upload a file to Azure Blob Storage
        Returns the URL of the uploaded blob
        """
        try:
            if not blob_name:
                blob_name = os.path.basename(file_path)

            container_client = self.blob_service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)

            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)

            # Generate a SAS token for temporary access
            sas_token = self._generate_sas_token(blob_name)
            blob_url = f"{blob_client.url}?{sas_token}"
            
            logger.info(f"File uploaded successfully: {blob_url}")
            return blob_url

        except Exception as e:
            logger.error(f"Error uploading file to Azure Storage: {str(e)}")
            raise

    def _generate_sas_token(self, blob_name: str) -> str:
        """Generate a SAS token for the blob"""
        from datetime import datetime, timedelta
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions

        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self.blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
        )
        return sas_token

    async def delete_file(self, blob_name: str):
        """Delete a file from Azure Blob Storage"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.delete_blob(blob_name)
            logger.info(f"File deleted successfully: {blob_name}")
        except Exception as e:
            logger.error(f"Error deleting file from Azure Storage: {str(e)}")
            raise 