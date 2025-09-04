# AI Study Assistant 🧠📚

A comprehensive, modern study toolkit powered by advanced NLP and AI technologies. Transform your learning experience with intelligent content processing, interactive study modes, and personalized analytics.

## ✨ Features

### 🎯 Core Study Tools
- **📝 Smart Summarization** - Condense long texts using T5 transformer models
- **🃏 Interactive Flashcards** - Auto-generate and review flashcards with spaced repetition
- **❓ Dynamic Quizzes** - Create multiple-choice questions with adaptive difficulty
- **🔑 Keyword Extraction** - Identify key terms and concepts automatically
- **🔄 Content Paraphrasing** - Rewrite and simplify complex text

### 🚀 Advanced Features
- **📸 Visual Question Answering** - Upload images and ask questions about them
- **📊 Learning Analytics** - Track progress, performance, and study patterns
- **🧠 Adaptive Learning** - Personalized difficulty adjustment based on performance
- **⏱️ Performance Tracking** - Monitor response times and accuracy
- **🎨 Modern UI** - Beautiful, responsive interface with dark theme

### 🛠️ Technical Highlights
- **Backend**: Flask API with SQLite database for session management
- **Frontend**: React + TypeScript + Tailwind CSS
- **AI Models**: T5, BLIP, and custom NLP pipelines
- **Real-time**: Session tracking and performance analytics
- **Responsive**: Mobile-first design with touch-friendly interactions

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Clone and navigate to backend**
   ```bash
   git clone <repository-url>
   cd ai-study-assistant/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the API server**
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:5173`

## 📁 Project Structure

```
ai-study-assistant/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── services/             # AI service modules
│   │   ├── summarizer.py     # Text summarization
│   │   ├── flashcards.py     # Flashcard generation
│   │   ├── quiz.py          # Quiz creation
│   │   ├── keywords.py      # Keyword extraction
│   │   ├── paraphrase.py    # Text paraphrasing
│   │   ├── visual_qa.py     # Visual question answering
│   │   ├── performance_tracker.py  # Analytics tracking
│   │   └── adaptive_learning.py    # Adaptive algorithms
│   └── utils/               # Utility functions
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── FlashcardReview.tsx
│   │   │   ├── VisualQA.tsx
│   │   │   └── AnalyticsDashboard.tsx
│   │   ├── lib/            # Utilities and API client
│   │   ├── App.tsx         # Main application
│   │   └── main.tsx        # Entry point
│   ├── package.json        # Node dependencies
│   └── tailwind.config.js  # Tailwind configuration
└── README.md
```

## 🎮 Usage Guide

### 1. Text Processing
- Paste your study material into the input area
- Choose from Summarize, Keywords, or Paraphrase tools
- Get instant AI-powered results

### 2. Interactive Learning
- Generate flashcards from your content
- Use Review Mode for spaced repetition practice
- Take adaptive quizzes with difficulty adjustment

### 3. Visual Learning
- Upload images (diagrams, equations, charts)
- Ask questions about the visual content
- Get AI-powered explanations and analysis

### 4. Track Progress
- View comprehensive analytics dashboard
- Monitor study streaks and performance
- Analyze subject-specific progress

## 🔧 API Endpoints

### Core Features
- `POST /summarize` - Text summarization
- `POST /flashcards` - Generate flashcards
- `POST /quiz` - Create quizzes
- `POST /keywords` - Extract keywords
- `POST /paraphrase` - Paraphrase text

### Advanced Features
- `POST /visual-qa` - Visual question answering
- `POST /session/create` - Create study session
- `GET /performance/{session_id}` - Get analytics
- `POST /flashcards/review` - Track flashcard performance
- `POST /quiz/submit` - Submit quiz answers

## 🎨 Customization

### Themes
The app uses a modern dark theme with customizable colors. Modify `tailwind.config.js` to change the color scheme.

### AI Models
Backend services can be configured to use different models:
- T5 variants for summarization and paraphrasing
- BLIP models for visual question answering
- Custom keyword extraction algorithms

## 🚀 Deployment

### Backend Deployment
1. Set up a Python hosting service (Heroku, Railway, etc.)
2. Configure environment variables
3. Deploy with `gunicorn app:app`

### Frontend Deployment
1. Build the production bundle: `npm run build`
2. Deploy to Vercel, Netlify, or similar
3. Configure API URL in environment variables

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Hugging Face Transformers for AI models
- React and TypeScript communities
- Tailwind CSS for styling framework
- Lucide React for beautiful icons