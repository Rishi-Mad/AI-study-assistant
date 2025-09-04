import { fetchJSON } from "./http";
import type {
  SummarizeReq, SummarizeResp,
  FlashcardsReq, FlashcardsResp,
  QuizReq, QuizResp,
  KeywordsReq, KeywordsResp,
  ParaphraseReq, ParaphraseResp
} from "./types";

function postJSON<T>(path: string, body: unknown) {
  return fetchJSON<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export const api = {
  summarize : (d: SummarizeReq)  => postJSON<SummarizeResp> ("/api/v1/summarize",  d),
  flashcards: (d: FlashcardsReq)  => postJSON<FlashcardsResp>("/api/v1/flashcards", d),
  quiz      : (d: QuizReq)        => postJSON<QuizResp>      ("/api/v1/quiz",       d),
  keywords  : (d: KeywordsReq)    => postJSON<KeywordsResp>  ("/api/v1/keywords",   d),
  paraphrase: (d: ParaphraseReq)  => postJSON<ParaphraseResp>("/api/v1/paraphrase", d),
};
