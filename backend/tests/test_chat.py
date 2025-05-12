import asyncio
import aiohttp
import os
from pathlib import Path

async def test_chat():
    async with aiohttp.ClientSession() as session:
        # Test 1: Basic chat with packaging issue
        print("\nTest 1: Basic chat with packaging issue")
        response = await session.post(
            "http://localhost:8000/api/v1/chat",
            json={
                "message": "My food was spilled and the box was broken",
                "metadata": {}
            }
        )
        result = await response.json()
        print("Response:", result)

        # Test 2: Chat with image upload
        print("\nTest 2: Chat with image upload")
        # First upload an image
        test_image_path = Path(__file__).parent / "test_data" / "test_image.jpg"
        if not test_image_path.exists():
            print("Please create a test image at:", test_image_path)
            return

        with open(test_image_path, "rb") as f:
            files = {"file": f}
            upload_response = await session.post(
                "http://localhost:8000/api/v1/upload-image",
                data=files
            )
            upload_result = await upload_response.json()
            print("Upload result:", upload_result)

            # Now send a chat message with the image
            chat_response = await session.post(
                "http://localhost:8000/api/v1/chat",
                json={
                    "message": "Here's a picture of my spilled food",
                    "metadata": {
                        "image_url": upload_result["filepath"]
                    }
                }
            )
            chat_result = await chat_response.json()
            print("Chat response:", chat_result)

if __name__ == "__main__":
    # Create test data directory if it doesn't exist
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # Run the tests
    asyncio.run(test_chat()) 