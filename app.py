from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow requests from other origins (e.g., Vite dev server)

@app.get("/")
def home():
    return {"message": "AI Study Assistant backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True)
