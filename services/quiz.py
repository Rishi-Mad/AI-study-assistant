import random
from typing import List, Dict
from services.flashcards import extract_flashcards

def build_quiz(text: str, max_qs: int = 5) -> List[Dict]:
    """
    Turn flashcards into multiple-choice questions.
    Each has 1 correct answer + 3 distractors from other answers.
    """
    cards = extract_flashcards(text, max_cards=max_qs * 2)
    if not cards:
        return []

    quiz = []
    answers_pool = [c["answer"] for c in cards]

    for c in cards[:max_qs]:
        correct = c["answer"]

        distractors = [a for a in answers_pool if a != correct]
        if len(distractors) < 3:
            continue

        wrong = random.sample(distractors, 3)
        choices = wrong + [correct]
        random.shuffle(choices)

        quiz.append({
            "question": c["question"],
            "choices": choices,
            "answer": correct,
            "term": c["term"]
        })

    return quiz
