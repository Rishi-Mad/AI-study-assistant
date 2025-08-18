export type SummarizeReq  = { text: string; min_length?: number; max_length?: number };
export type FlashcardsReq = { text: string; max_cards?: number };
export type QuizReq       = { text: string; max_qs?: number };
export type KeywordsReq   = { text: string; top_k?: number };
export type ParaphraseReq = { text: string; max_length?: number };

export type SummarizeResp = {
  model: string;
  summary: string;
};

export type Flashcard = {
  term: string;
  question: string;
  answer: string;
};

export type FlashcardsResp = {
  model: string;
  count: number;
  cards: Flashcard[];
};

export type QuizItem = {
  question: string;
  choices: string[];
  answer: string;
  term: string;
};

export type QuizResp = {
  model: string;
  count: number;
  quiz: QuizItem[];
};

export type KeywordItem = {
  keyword: string;
  score: number;
};

export type KeywordsResp = {
  model: string;
  keywords: KeywordItem[];
  count?: number;
};

export type ParaphraseResp = {
  model: string;
  paraphrase: string;
};
