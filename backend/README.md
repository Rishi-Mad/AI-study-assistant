# AI Study Assistant - FastAPI Backend

A comprehensive AI-powered study assistant with advanced features for learning and retention.

## 🚀 Features

- **Text Summarization**: AI-powered text summarization using T5 models
- **Flashcard Generation**: Intelligent flashcard creation from study materials
- **Quiz Generation**: Automated quiz creation with multiple question types
- **Keyword Extraction**: Key concept identification and extraction
- **Text Paraphrasing**: AI-powered text rephrasing for better understanding
- **Visual Question Answering**: Answer questions about uploaded images
- **Adaptive Learning**: Personalized learning recommendations
- **Performance Analytics**: Track learning progress and performance

## 🛠️ Technology Stack

- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **AI Models**: 
  - T5 (Text-to-Text Transfer Transformer) for summarization and paraphrasing
  - BLIP (Bootstrapping Language-Image Pre-training) for visual QA
  - spaCy for NLP processing
- **Authentication**: Session-based tracking
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## 📋 API Endpoints

### Core Features
- `POST /api/v1/summarize` - Text summarization
- `POST /api/v1/flashcards` - Generate flashcards
- `POST /api/v1/quiz` - Create quizzes
- `POST /api/v1/keywords` - Extract keywords
- `POST /api/v1/paraphrase` - Paraphrase text
- `POST /api/v1/visual-qa` - Visual question answering

### Session Management
- `POST /api/v1/sessions/create` - Create study session
- `GET /api/v1/sessions/{session_id}` - Get session info
- `DELETE /api/v1/sessions/{session_id}` - End session

### Analytics
- `GET /api/v1/analytics/{session_id}` - Get learning analytics

## 🚀 Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. **Run the server**:
   ```bash
   python main.py
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Deployment

```bash
# Build the image
docker build -t ai-study-assistant .

# Run the container
docker run -p 8000:8000 ai-study-assistant
```

### Hugging Face Spaces

This backend is configured for deployment on Hugging Face Spaces:

1. Create a new Space on Hugging Face
2. Upload the backend code
3. The `app.yaml` file configures the Space automatically
4. Models will be downloaded on first startup

## 📊 Database Schema

The application uses SQLite with the following main tables:

- **users**: User information and preferences
- **user_sessions**: Study session tracking
- **study_activities**: Activity logging and performance
- **study_content**: Generated content storage
- **flashcard_performance**: Flashcard review tracking
- **quiz_performance**: Quiz attempt tracking
- **learning_analytics**: Aggregated learning insights

## 🔧 Configuration

Environment variables can be set in `.env` file:

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./study_assistant.db
HUGGINGFACE_CACHE_DIR=./models
MAX_TEXT_LENGTH=5000
DEFAULT_SUMMARY_LENGTH=100
```

## 📈 Performance Features

- **Model Caching**: AI models are loaded once and cached in memory
- **Async Processing**: Non-blocking API endpoints
- **Database Optimization**: Efficient queries with SQLAlchemy
- **Error Handling**: Comprehensive error handling and logging
- **Rate Limiting**: Built-in request throttling

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_summarization.py
```

## 📝 API Usage Examples

### Summarize Text
```bash
curl -X POST "http://localhost:8000/api/v1/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your study material here...",
    "min_length": 50,
    "max_length": 150,
    "session_id": "optional-session-id"
  }'
```

### Generate Flashcards
```bash
curl -X POST "http://localhost:8000/api/v1/flashcards" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your study material here...",
    "max_cards": 10,
    "difficulty_level": "medium",
    "session_id": "optional-session-id"
  }'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the logs in the `logs/` directory
