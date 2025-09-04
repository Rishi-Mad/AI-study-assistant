export type SummarizeReq  = { text: string; min_length?: number; max_length?: number; session_id?: string };
export type FlashcardsReq = { text: string; max_cards?: number; session_id?: string; difficulty_level?: string };
export type QuizReq       = { text: string; max_qs?: number; session_id?: string; difficulty_level?: string };
export type KeywordsReq   = { text: string; top_k?: number; session_id?: string };
export type ParaphraseReq = { text: string; max_length?: number; session_id?: string };

export type SummarizeResp = {
  model: string;
  summary: string;
  metadata?: {
    input_length: number;
    summary_length: number;
    compression_ratio: number;
  };
};

export type Flashcard = {
  term: string;
  question: string;
  answer: string;
  quality_score?: number;
  difficulty_level?: number;
};

export type FlashcardsResp = {
  count: number;
  cards: Flashcard[];
  metadata?: {
    difficulty_level: string;
    avg_quality_score: number;
  };
};

export type QuizItem = {
  question: string;
  choices: string[];
  answer: string;
  term: string;
};

export type QuizResp = {
  count: number;
  quiz: QuizItem[];
  metadata?: {
    difficulty_level: string;
  };
};

export type KeywordItem = {
  keyword: string;
  score: number;
};

export type KeywordsResp = {
  count: number;
  keywords: KeywordItem[];
};

export type ParaphraseResp = {
  model: string;
  paraphrase: string;
};
