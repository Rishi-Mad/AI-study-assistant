import { useState, useEffect } from "react";
import { cn } from "../lib/utils";
import { ChevronLeft, ChevronRight, RotateCcw, CheckCircle, XCircle } from "lucide-react";
import type { Flashcard } from "../lib/types";

interface FlashcardReviewProps {
  cards: Flashcard[];
  onReviewComplete?: (results: ReviewResult[]) => void;
}

interface ReviewResult {
  cardIndex: number;
  isCorrect: boolean;
  responseTime: number;
  attempts: number;
}

export default function FlashcardReview({ cards, onReviewComplete }: FlashcardReviewProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [userAnswer, setUserAnswer] = useState("");
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [reviewResults, setReviewResults] = useState<ReviewResult[]>([]);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [attempts, setAttempts] = useState(0);

  const currentCard = cards[currentIndex];
  const progress = ((currentIndex + 1) / cards.length) * 100;

  useEffect(() => {
    setStartTime(Date.now());
    setAttempts(0);
    setIsFlipped(false);
    setShowResult(false);
    setUserAnswer("");
  }, [currentIndex]);

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const handleAnswerSubmit = () => {
    if (!userAnswer.trim()) return;

    const responseTime = (Date.now() - startTime) / 1000;
    const correct = userAnswer.toLowerCase().trim() === currentCard.answer.toLowerCase().trim();
    
    setIsCorrect(correct);
    setShowResult(true);
    
    const result: ReviewResult = {
      cardIndex: currentIndex,
      isCorrect: correct,
      responseTime,
      attempts: attempts + 1
    };
    
    setReviewResults(prev => [...prev, result]);
  };

  const handleNext = () => {
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // Review complete
      onReviewComplete?.(reviewResults);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleRetry = () => {
    setAttempts(prev => prev + 1);
    setUserAnswer("");
    setShowResult(false);
    setStartTime(Date.now());
  };

  if (!currentCard) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center">
        <CheckCircle className="h-12 w-12 text-green-400 mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">Review Complete!</h3>
        <p className="text-white/60 mb-6">
          You've reviewed all {cards.length} flashcards
        </p>
        <div className="text-sm text-white/60">
          Correct: {reviewResults.filter(r => r.isCorrect).length} / {reviewResults.length}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="w-full bg-white/10 rounded-full h-2">
        <div 
          className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Card Counter */}
      <div className="text-center text-sm text-white/60">
        Card {currentIndex + 1} of {cards.length}
      </div>

      {/* Flashcard */}
      <div className="relative">
        <div 
          className={cn(
            "card h-64 cursor-pointer transition-all duration-500 transform-gpu",
            isFlipped && "rotate-y-180"
          )}
          onClick={handleFlip}
        >
          <div className="absolute inset-0 backface-hidden">
            <div className="h-full flex flex-col justify-center items-center text-center p-6">
              <div className="text-xs text-white/60 mb-2">{currentCard.term}</div>
              <h3 className="text-lg font-semibold text-white mb-4">
                {currentCard.question}
              </h3>
              <div className="text-sm text-white/60">
                Click to reveal answer
              </div>
            </div>
          </div>
          
          <div className="absolute inset-0 backface-hidden rotate-y-180">
            <div className="h-full flex flex-col justify-center items-center text-center p-6">
              <div className="text-xs text-white/60 mb-2">Answer</div>
              <div className="text-lg text-green-300 font-medium">
                {currentCard.answer}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Answer Input */}
      {isFlipped && !showResult && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Your Answer:
            </label>
            <input
              type="text"
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAnswerSubmit()}
              className="input-field"
              placeholder="Type your answer here..."
              autoFocus
            />
          </div>
          <button
            onClick={handleAnswerSubmit}
            disabled={!userAnswer.trim()}
            className="btn-primary w-full"
          >
            Submit Answer
          </button>
        </div>
      )}

      {/* Result Display */}
      {showResult && (
        <div className="space-y-4">
          <div className={cn(
            "p-4 rounded-lg border-2",
            isCorrect 
              ? "bg-green-500/20 border-green-500/30" 
              : "bg-red-500/20 border-red-500/30"
          )}>
            <div className="flex items-center space-x-2 mb-2">
              {isCorrect ? (
                <CheckCircle className="h-5 w-5 text-green-400" />
              ) : (
                <XCircle className="h-5 w-5 text-red-400" />
              )}
              <span className={cn(
                "font-medium",
                isCorrect ? "text-green-300" : "text-red-300"
              )}>
                {isCorrect ? "Correct!" : "Incorrect"}
              </span>
            </div>
            <div className="text-sm text-white/80">
              Your answer: "{userAnswer}"
            </div>
            {!isCorrect && (
              <div className="text-sm text-green-300 mt-1">
                Correct answer: "{currentCard.answer}"
              </div>
            )}
          </div>

          <div className="flex space-x-3">
            {!isCorrect && (
              <button
                onClick={handleRetry}
                className="btn-secondary flex-1 flex items-center justify-center space-x-2"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Try Again</span>
              </button>
            )}
            <button
              onClick={handleNext}
              className="btn-primary flex-1"
            >
              {currentIndex < cards.length - 1 ? "Next Card" : "Finish Review"}
            </button>
          </div>
        </div>
      )}

      {/* Navigation */}
      {!showResult && (
        <div className="flex justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className={cn(
              "btn-secondary flex items-center space-x-2",
              currentIndex === 0 && "opacity-50 cursor-not-allowed"
            )}
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Previous</span>
          </button>
          
          <button
            onClick={handleNext}
            disabled={currentIndex === cards.length - 1}
            className={cn(
              "btn-secondary flex items-center space-x-2",
              currentIndex === cards.length - 1 && "opacity-50 cursor-not-allowed"
            )}
          >
            <span>Skip</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}