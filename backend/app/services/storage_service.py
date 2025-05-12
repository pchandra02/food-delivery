import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

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