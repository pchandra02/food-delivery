from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import chat

app = FastAPI(title="Food Delivery Support Chat")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Food Delivery Support Chat API"} 