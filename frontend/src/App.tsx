import { useState } from "react";
import { api } from "./lib/api";
import type {
  FlashcardsResp,
  KeywordsResp,
  ParaphraseResp,
  QuizResp,
  SummarizeResp,
} from "./lib/types";


type Tab = "Summarize" | "Flashcards" | "Quiz" | "Keywords" | "Paraphrase";

export default function App() {
  const [tab, setTab] = useState<Tab>("Summarize");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // per-feature outputs
  const [sumOut, setSumOut] = useState<SummarizeResp | null>(null);
  const [fcOut,  setFcOut]  = useState<FlashcardsResp | null>(null);
  const [quizOut,setQuizOut]= useState<QuizResp | null>(null);
  const [kwOut,  setKwOut]  = useState<KeywordsResp | null>(null);
  const [paraOut,setParaOut]= useState<ParaphraseResp | null>(null);

  async function run() {
    setError(null);
    setSumOut(null); setFcOut(null); setQuizOut(null); setKwOut(null); setParaOut(null);

    const clean = text.trim();
    if (!clean) { setError("Please paste some text first."); return; }

    setLoading(true);
    try {
      if (tab === "Summarize") {
        const r = await api.summarize({ text: clean, min_length: 40, max_length: 140 });
        setSumOut(r);
      } else if (tab === "Flashcards") {
        const r = await api.flashcards({ text: clean, max_cards: 10 });
        setFcOut(r);
      } else if (tab === "Quiz") {
        const r = await api.quiz({ text: clean, max_qs: 5 });
        setQuizOut(r);
      } else if (tab === "Keywords") {
        const r = await api.keywords({ text: clean, top_k: 10 });
        setKwOut(r);
      } else if (tab === "Paraphrase") {
        const r = await api.paraphrase({ text: clean, max_length: 120 });
        setParaOut(r);
      }
    } catch (e: any) {
      setError(e.message ?? "Request failed");
    } finally {
      setLoading(false);
    }
  }

  const tabs: Tab[] = ["Summarize", "Flashcards", "Quiz", "Keywords", "Paraphrase"];

  return (
    <div style={{ minHeight: "100vh", background: "#0b0e14", color: "white", padding: "24px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600 }}>AI Study Assistant</h1>
        <p style={{ opacity: 0.8, marginTop: 4 }}>
          TypeScript + React + Vite · Backend: {import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"}
        </p>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
          {tabs.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid #3a3f55",
                background: tab === t ? "white" : "transparent",
                color: tab === t ? "black" : "white"
              }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* IO */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
          <div>
            <label style={{ fontSize: 12, opacity: 0.8 }}>Input text</label>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              rows={14}
              placeholder="Paste notes, textbook sections, or articles…"
              style={{
                width: "100%", marginTop: 6, padding: 12, borderRadius: 10,
                border: "1px solid #3a3f55", background: "#101522", color: "white"
              }}
            />
            <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
              <button
                onClick={run}
                disabled={loading}
                style={{
                  padding: "8px 14px", borderRadius: 8, border: "none",
                  background: "#6366f1", color: "white", opacity: loading ? 0.6 : 1
                }}
              >
                {loading ? "Working…" : `Run ${tab}`}
              </button>
              <button
                onClick={() => { setText(""); setSumOut(null); setFcOut(null); setQuizOut(null); setKwOut(null); setParaOut(null); setError(null); }}
                style={{ padding: "8px 14px", borderRadius: 8, background: "transparent", border: "1px solid #3a3f55", color: "white" }}
              >
                Clear
              </button>
            </div>
            {error && <p style={{ color: "#fca5a5", marginTop: 8, fontSize: 14 }}>{error}</p>}
          </div>

          <div>
            <label style={{ fontSize: 12, opacity: 0.8 }}>Result</label>
            <div style={{ marginTop: 6, padding: 12, borderRadius: 10, border: "1px solid #3a3f55", background: "#101522" }}>
              {/* Summarize */}
              {tab === "Summarize" && sumOut && (
                <>
                  <p style={{ opacity: 0.7, fontSize: 12, marginTop: 0 }}>Model: {sumOut.model}</p>
                  <div>{sumOut.summary}</div>
                </>
              )}

              {/* Flashcards */}
              {tab === "Flashcards" && fcOut && (
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {fcOut.cards.map((c, i) => (
                    <li key={i} style={{ border: "1px solid #2c3145", borderRadius: 8, padding: 10, marginBottom: 8 }}>
                      <div style={{ opacity: 0.7, fontSize: 12 }}>{c.term}</div>
                      <div style={{ fontWeight: 600 }}>{c.question}</div>
                      <div style={{ color: "#86efac" }}>{c.answer}</div>
                    </li>
                  ))}
                  {fcOut.cards.length === 0 && <div style={{ opacity: 0.8 }}>No cards found.</div>}
                </ul>
              )}

              {/* Quiz */}
              {tab === "Quiz" && quizOut && (
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {quizOut.quiz.map((q, i) => (
                    <li key={i} style={{ border: "1px solid #2c3145", borderRadius: 8, padding: 10, marginBottom: 12 }}>
                      <div style={{ fontWeight: 600, marginBottom: 6 }}>{q.question}</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                        {q.choices.map((c, j) => (
                          <span key={j} style={{ border: "1px solid #2c3145", borderRadius: 6, padding: 6 }}>{c}</span>
                        ))}
                      </div>
                      <div style={{ color: "#86efac", fontSize: 12, marginTop: 6 }}>Answer: {q.answer}</div>
                    </li>
                  ))}
                  {quizOut.quiz.length === 0 && <div style={{ opacity: 0.8 }}>No questions generated.</div>}
                </ul>
              )}

              {/* Keywords */}
              {tab === "Keywords" && kwOut && (
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {kwOut.keywords.map((k, i) => (
                    <span key={i} style={{ padding: "4px 8px", borderRadius: 8, border: "1px solid #2c3145" }}>
                      {k.keyword} <span style={{ opacity: 0.6 }}>({k.score})</span>
                    </span>
                  ))}
                  {kwOut.keywords.length === 0 && <div style={{ opacity: 0.8 }}>No keywords found.</div>}
                </div>
              )}

              {/* Paraphrase */}
              {tab === "Paraphrase" && paraOut && (
                <div>{paraOut.paraphrase}</div>
              )}

              {/* Empty state */}
              {!sumOut && !fcOut && !quizOut && !kwOut && !paraOut && (
                <div style={{ opacity: 0.8 }}>Results will appear here.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
