from typing import Dict, Any
import json
import redis
from app.core.config import settings

class QueueService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.queue_name = settings.QUEUE_NAME

    async def push_to_queue(self, ticket_data: Dict[str, Any]) -> bool:
        """Push a ticket to the queue for human agent processing."""
        try:
            # Convert ticket data to JSON string
            ticket_json = json.dumps(ticket_data)
            
            # Push to Redis list
            self.redis_client.lpush(self.queue_name, ticket_json)
            
            # Optional: Set expiry on the ticket (e.g., 7 days)
            ticket_key = f"ticket:{ticket_data['ticket_id']}"
            self.redis_client.setex(
                ticket_key,
                60 * 60 * 24 * 7,  # 7 days in seconds
                ticket_json
            )
            
            return True
        except Exception as e:
            print(f"Error pushing to queue: {str(e)}")
            return False

    async def get_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        """Get the current status of a ticket from Redis."""
        try:
            ticket_key = f"ticket:{ticket_id}"
            ticket_data = self.redis_client.get(ticket_key)
            
            if ticket_data:
                return json.loads(ticket_data)
            return {"status": "not_found"}
        except Exception as e:
            print(f"Error getting ticket status: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def update_ticket_status(
        self,
        ticket_id: str,
        status: str,
        resolution: str = None
    ) -> bool:
        """Update the status of a ticket in Redis."""
        try:
            ticket_key = f"ticket:{ticket_id}"
            ticket_data = self.redis_client.get(ticket_key)
            
            if not ticket_data:
                return False
            
            ticket_dict = json.loads(ticket_data)
            ticket_dict["status"] = status
            if resolution:
                ticket_dict["resolution"] = resolution
            
            # Update Redis
            self.redis_client.setex(
                ticket_key,
                60 * 60 * 24 * 7,  # 7 days in seconds
                json.dumps(ticket_dict)
            )
            
            return True
        except Exception as e:
            print(f"Error updating ticket status: {str(e)}")
            return False 