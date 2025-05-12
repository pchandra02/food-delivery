# Food Delivery AI Customer Support Chatbot

An intelligent chatbot system for handling customer support issues in food delivery platforms.

## Features

- AI-powered issue classification and analysis
- Image analysis for packaging and food quality issues
- Order validation and verification
- Multilingual support (English and Arabic)
- Integration with backend customer support system
- Automated response generation
- Queue-based escalation system

## Issue Categories Handled

1. Packaging / Spillage
2. Missing / Incorrect Items
3. Food Quality / Quantity
4. Order Cancellation
5. Refund Related Queries
6. Delivery Address Issues
7. Vendor Issues
8. Rider Issues
9. Delivery Status
10. Escalation to Human Support

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Architecture

The application follows a clean architecture pattern with the following components:

- `app/`: Main application package
  - `api/`: API routes and endpoints
  - `core/`: Core business logic
  - `models/`: Data models and schemas
  - `services/`: Service layer for AI and business logic
  - `utils/`: Utility functions
  - `config/`: Configuration management

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 