import { useState, useEffect } from "react";
import { api } from "./lib/api";
import { cn, generateSessionId } from "./lib/utils";
import FlashcardReview from "./components/FlashcardReview";
import VisualQA from "./components/VisualQA";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import { 
  Brain, 
  BookOpen, 
  FileText, 
  HelpCircle, 
  Lightbulb, 
  RefreshCw,
  Sparkles,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Camera,
  BarChart3,
  Settings,
  Play
} from "lucide-react";
import type {
  FlashcardsResp,
  KeywordsResp,
  ParaphraseResp,
  QuizResp,
  SummarizeResp,
} from "./lib/types";

type Tab = "Summarize" | "Flashcards" | "Quiz" | "Keywords" | "Paraphrase" | "VisualQA" | "Analytics";

interface TabConfig {
  id: Tab;
  label: string;
  icon: React.ComponentType<any>;
  description: string;
  color: string;
}

const tabs: TabConfig[] = [
  { id: "Summarize", label: "Summarize", icon: FileText, description: "Condense long texts", color: "from-blue-500 to-cyan-500" },
  { id: "Flashcards", label: "Flashcards", icon: BookOpen, description: "Create study cards", color: "from-green-500 to-emerald-500" },
  { id: "Quiz", label: "Quiz", icon: HelpCircle, description: "Generate questions", color: "from-purple-500 to-violet-500" },
  { id: "Keywords", label: "Keywords", icon: Lightbulb, description: "Extract key terms", color: "from-orange-500 to-amber-500" },
  { id: "Paraphrase", label: "Paraphrase", icon: RefreshCw, description: "Rewrite content", color: "from-pink-500 to-rose-500" },
  { id: "VisualQA", label: "Visual QA", icon: Camera, description: "Answer image questions", color: "from-indigo-500 to-blue-500" },
  { id: "Analytics", label: "Analytics", icon: BarChart3, description: "View progress", color: "from-teal-500 to-green-500" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("Summarize");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [studyStats] = useState({
    totalSessions: 0,
    totalCards: 0,
    totalQuizzes: 0,
    streak: 0
  });
  const [showFlashcardReview, setShowFlashcardReview] = useState(false);

  // per-feature outputs
  const [sumOut, setSumOut] = useState<SummarizeResp | null>(null);
  const [fcOut, setFcOut] = useState<FlashcardsResp | null>(null);
  const [quizOut, setQuizOut] = useState<QuizResp | null>(null);
  const [kwOut, setKwOut] = useState<KeywordsResp | null>(null);
  const [paraOut, setParaOut] = useState<ParaphraseResp | null>(null);

  // Initialize session on component mount
  useEffect(() => {
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
  }, []);

  async function run() {
    setError(null);
    setSumOut(null); setFcOut(null); setQuizOut(null); setKwOut(null); setParaOut(null);

    const clean = text.trim();
    if (!clean) { setError("Please paste some text first."); return; }

    setLoading(true);
    try {
      if (activeTab === "Summarize") {
        const r = await api.summarize({ text: clean, min_length: 40, max_length: 140, session_id: sessionId });
        setSumOut(r);
      } else if (activeTab === "Flashcards") {
        const r = await api.flashcards({ text: clean, max_cards: 10, session_id: sessionId });
        setFcOut(r);
      } else if (activeTab === "Quiz") {
        const r = await api.quiz({ text: clean, max_qs: 5, session_id: sessionId });
        setQuizOut(r);
      } else if (activeTab === "Keywords") {
        const r = await api.keywords({ text: clean, top_k: 10, session_id: sessionId });
        setKwOut(r);
      } else if (activeTab === "Paraphrase") {
        const r = await api.paraphrase({ text: clean, max_length: 120, session_id: sessionId });
        setParaOut(r);
      }
    } catch (e: any) {
      setError(e.message ?? "Request failed");
    } finally {
      setLoading(false);
    }
  }

  function clearAll() {
    setText("");
    setSumOut(null);
    setFcOut(null);
    setQuizOut(null);
    setKwOut(null);
    setParaOut(null);
    setError(null);
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">AI Study Assistant</h1>
                <p className="text-xs text-white/60">Powered by Advanced NLP</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="hidden sm:flex items-center space-x-4 text-sm text-white/80">
                <div className="flex items-center space-x-1">
                  <TrendingUp className="h-4 w-4" />
                  <span>{studyStats.streak} day streak</span>
                </div>
                <div className="flex items-center space-x-1">
                  <BookOpen className="h-4 w-4" />
                  <span>{studyStats.totalCards} cards</span>
                </div>
              </div>
              <button className="p-2 glass rounded-lg hover:bg-white/20 transition-colors">
                <Settings className="h-5 w-5 text-white" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "group relative p-4 rounded-xl transition-all duration-200",
                    isActive 
                      ? "glass-dark shadow-lg scale-105" 
                      : "glass hover:bg-white/20 hover:scale-105"
                  )}
                >
                  <div className="flex flex-col items-center space-y-2">
                    <div className={cn(
                      "p-2 rounded-lg transition-all duration-200",
                      isActive 
                        ? `bg-gradient-to-r ${tab.color}` 
                        : "bg-white/10 group-hover:bg-white/20"
                    )}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <div className="text-center">
                      <div className={cn(
                        "text-sm font-medium transition-colors",
                        isActive ? "text-white" : "text-white/80"
                      )}>
                        {tab.label}
                      </div>
                      <div className="text-xs text-white/60 mt-1">
                        {tab.description}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="space-y-6">
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Input Content</h2>
                <div className="flex items-center space-x-2 text-sm text-white/60">
                  <Clock className="h-4 w-4" />
                  <span>Session: {sessionId.slice(-8)}</span>
                </div>
              </div>
              
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={12}
                placeholder="Paste your study material, notes, textbook sections, or articles here..."
                className="input-field resize-none"
              />
              
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-white/60">
                  {text.length} characters
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={clearAll}
                    className="btn-secondary"
                  >
                    Clear
                  </button>
                  <button
                    onClick={run}
                    disabled={loading || !text.trim()}
                    className={cn(
                      "btn-primary flex items-center space-x-2",
                      (loading || !text.trim()) && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                        <span>Processing...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        <span>Generate {activeTab}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
              
              {error && (
                <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <XCircle className="h-4 w-4 text-red-400" />
                    <span className="text-red-300 text-sm">{error}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Output Section */}
          <div className="space-y-6">
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Results</h2>
                <div className="text-sm text-white/60">
                  {activeTab} Output
                </div>
              </div>
              
              <div className="min-h-[400px]">
                {/* Summarize Results */}
                {activeTab === "Summarize" && sumOut && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center space-x-2 text-sm text-white/60">
                      <CheckCircle className="h-4 w-4 text-green-400" />
                      <span>Model: {sumOut.model}</span>
                    </div>
                    <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                      <p className="text-white leading-relaxed">{sumOut.summary}</p>
                    </div>
                    {sumOut.metadata && (
                      <div className="text-xs text-white/60">
                        Compression ratio: {sumOut.metadata.compression_ratio}x
                      </div>
                    )}
                  </div>
                )}

                {/* Flashcards Results */}
                {activeTab === "Flashcards" && fcOut && !showFlashcardReview && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-sm text-white/60">
                        <CheckCircle className="h-4 w-4 text-green-400" />
                        <span>{fcOut.count} flashcards generated</span>
                      </div>
                      <button
                        onClick={() => setShowFlashcardReview(true)}
                        className="btn-primary flex items-center space-x-2"
                      >
                        <Play className="h-4 w-4" />
                        <span>Review Mode</span>
                      </button>
                    </div>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {fcOut.cards.map((card, i) => (
                        <div key={i} className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors">
                          <div className="text-xs text-white/60 mb-2">{card.term}</div>
                          <div className="font-medium text-white mb-2">{card.question}</div>
                          <div className="text-green-300 text-sm">{card.answer}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Flashcard Review Mode */}
                {activeTab === "Flashcards" && fcOut && showFlashcardReview && (
                  <div className="animate-fade-in">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Flashcard Review</h3>
                      <button
                        onClick={() => setShowFlashcardReview(false)}
                        className="btn-secondary"
                      >
                        Back to List
                      </button>
                    </div>
                    <FlashcardReview 
                      cards={fcOut.cards}
                      onReviewComplete={(results) => {
                        console.log("Review completed:", results);
                        setShowFlashcardReview(false);
                        // Here you could send results to backend for tracking
                      }}
                    />
                  </div>
                )}

                {/* Quiz Results */}
                {activeTab === "Quiz" && quizOut && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center space-x-2 text-sm text-white/60">
                      <CheckCircle className="h-4 w-4 text-green-400" />
                      <span>{quizOut.count} questions generated</span>
                    </div>
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {quizOut.quiz.map((question, i) => (
                        <div key={i} className="p-4 bg-white/5 rounded-lg border border-white/10">
                          <div className="font-medium text-white mb-3">{question.question}</div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
                            {question.choices.map((choice, j) => (
                              <div key={j} className="p-2 bg-white/5 rounded border border-white/10 text-sm">
                                {choice}
                              </div>
                            ))}
                          </div>
                          <div className="text-green-300 text-sm">
                            <strong>Answer:</strong> {question.answer}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Keywords Results */}
                {activeTab === "Keywords" && kwOut && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center space-x-2 text-sm text-white/60">
                      <CheckCircle className="h-4 w-4 text-green-400" />
                      <span>{kwOut.keywords.length} keywords extracted</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {kwOut.keywords.map((keyword, i) => (
                        <span 
                          key={i} 
                          className="px-3 py-1 bg-gradient-to-r from-orange-500/20 to-amber-500/20 border border-orange-500/30 rounded-full text-sm text-white"
                        >
                          {keyword.keyword}
                          <span className="text-orange-300 ml-1">({keyword.score.toFixed(2)})</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Paraphrase Results */}
                {activeTab === "Paraphrase" && paraOut && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center space-x-2 text-sm text-white/60">
                      <CheckCircle className="h-4 w-4 text-green-400" />
                      <span>Model: {paraOut.model}</span>
                    </div>
                    <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                      <p className="text-white leading-relaxed">{paraOut.paraphrase}</p>
                    </div>
                  </div>
                )}

                {/* Visual QA */}
                {activeTab === "VisualQA" && (
                  <div className="animate-fade-in">
                    <VisualQA onResult={(result) => {
                      console.log("Visual QA result:", result);
                      // Here you could send results to backend for tracking
                    }} />
                  </div>
                )}

                {/* Analytics Dashboard */}
                {activeTab === "Analytics" && (
                  <div className="animate-fade-in">
                    <AnalyticsDashboard sessionId={sessionId} />
                  </div>
                )}

                {/* Empty State */}
                {!sumOut && !fcOut && !quizOut && !kwOut && !paraOut && activeTab !== "VisualQA" && activeTab !== "Analytics" && (
                  <div className="flex flex-col items-center justify-center h-96 text-center">
                    <Sparkles className="h-12 w-12 text-white/40 mb-4" />
                    <h3 className="text-lg font-medium text-white mb-2">Ready to Study</h3>
                    <p className="text-white/60">Enter your content and click generate to get started</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
