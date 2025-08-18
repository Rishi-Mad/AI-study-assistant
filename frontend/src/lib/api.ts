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
  summarize : (d: SummarizeReq)  => postJSON<SummarizeResp> ("/summarize",  d),
  flashcards: (d: FlashcardsReq)  => postJSON<FlashcardsResp>("/flashcards", d),
  quiz      : (d: QuizReq)        => postJSON<QuizResp>      ("/quiz",       d),
  keywords  : (d: KeywordsReq)    => postJSON<KeywordsResp>  ("/keywords",   d),
  paraphrase: (d: ParaphraseReq)  => postJSON<ParaphraseResp>("/paraphrase", d),
};
