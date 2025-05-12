# Food Delivery Support System

A sophisticated support system for food delivery platforms that uses an agentic orchestration approach to handle customer issues efficiently.

## System Architecture

The system uses a multi-agent orchestration framework powered by LangGraph and LangChain, with specialized agents working together to process customer issues:

### Agent Pipeline

1. **Language Detection Agent**
   - Uses GPT-4 to detect the language of customer messages
   - Ensures proper handling of multilingual support
   - Outputs ISO 639-1 language codes

2. **Classification Agent**
   - Uses GPT-4 to categorize customer issues into predefined types:
     - Packaging/Spillage issues
     - Missing/Incorrect items
     - Food quality concerns
     - Refund/Cancellation requests
     - Rider/Vendor issues

3. **Image Review Agent**
   - Uses GPT-4 Vision to analyze images of food delivery issues
   - Detects packaging damage and spillage
   - Provides visual analysis of food quality issues

### Technology Stack

- **Backend**: FastAPI with Python
- **Frontend**: React with TypeScript and Vite
- **AI/ML**: 
  - LangChain for agent orchestration
  - OpenAI GPT-4 for language processing
  - OpenAI GPT-4 Vision for image analysis
- **Real-time Communication**: WebSocket for live updates

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key

### Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other configurations
   ```

4. Run the backend server:
   ```bash
   python run_server.py
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

## Features

- **Intelligent Issue Classification**: Automatically categorizes customer issues using GPT-4
- **Multilingual Support**: Detects and handles multiple languages
- **Image Analysis**: Analyzes food delivery images for quality and packaging issues
- **Real-time Updates**: WebSocket-based live updates for order status
- **Responsive UI**: Modern, mobile-friendly interface built with React and Chakra UI

## Agent Workflow

1. Customer submits an issue (text + optional image)
2. Language Detection Agent identifies the language
3. Classification Agent categorizes the issue
4. If an image is provided, Image Review Agent analyzes it
5. System generates appropriate response based on agent outputs
6. Customer receives real-time updates on their issue

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 