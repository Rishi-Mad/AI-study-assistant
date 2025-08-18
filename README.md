# AI-study-assistant 🧠📚

A lightweight, open-source **study toolkit** powered by NLP/AI:
- **Summarize** long notes (abstractive, T5)
- Auto-generate **Flashcards** (definition extraction)
- Build **Quizzes** (MCQ with distractors)
- Extract **Keywords** (unigram/bigram scoring)
- **Paraphrase** content (T5 text2text)

## ✨ Why this project
Designed to help students learn smarter, and to demonstrate practical **AI + API** skills (Flask, Transformers) in a clean, documented, deployable codebase.

---

## 🚀 Quickstart (Backend)

> Repo layout:
>
> ```
> ai-study-assistant/
> ├─ backend/
> │  ├─ app.py
> │  ├─ services/
> │  ├─ utils/
> │  └─ requirements.txt
> └─ frontend/ (coming soon)
> ```

1. **Create and activate a virtualenv**
   ```bash
   cd backend
   python -m venv venv
   # Windows (PowerShell):
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt

3. **Run the API**
    ```bash
    python app.py

