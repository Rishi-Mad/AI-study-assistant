import re
from typing import List, Dict, Set, Tuple
from utils.text import sentences, normalize_space
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

_DEF_PATTERNS = [
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+is\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+are\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+refers to\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+is defined as\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s*:\s*(.+)$",
    
    # Enhanced patterns for better recognition
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+means\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+represents\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+describes\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+can be described as\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+is known as\s+(.*)$",
    r"^\s*The term\s+([A-Z][A-Za-z0-9\- ]{1,60})\s+(.*)$",
    r"^\s*In\s+[\w\s]+,\s+([A-Z][A-Za-z0-9\- ]{1,60})\s+is\s+(.*)$",
]

def _clean_term(term: str) -> str:
    """Enhanced term cleaning with better edge case handling"""
    term = normalize_space(term)
    term = re.sub(r"[.:,;]+$", "", term)
    term = re.sub(r"^(the|a|an)\s+", "", term, flags=re.IGNORECASE)
    return term.strip()

def _clean_defn(defn: str) -> str:
    """Enhanced definition cleaning with context preservation"""
    defn = normalize_space(defn)
    patterns = [
        r"(.+?[.!?])(\s|$)",
        r"(.+?;)(\s|$)",
        r"(.+?)(?:\s+(?:However|But|Although|While))",
    ]
    
    for pattern in patterns:
        m = re.match(pattern, defn)
        if m:
            return m.group(1).strip()
    
    if len(defn) > 100:
        defn = defn[:100]
        last_space = defn.rfind(' ')
        if last_space > 50:
            defn = defn[:last_space] + "..."
    
    return defn.strip()

def _calculate_quality_score(term: str, answer: str, context: str = "") -> float:
    """Calculate quality score for flashcard based on multiple factors"""
    score = 1.0
    
    word_count = len(term.split())
    if word_count == 1:
        score += 0.2
    elif 2 <= word_count <= 3:
        score += 0.1
    else:
        score -= 0.1
    
    answer_length = len(answer.split())
    if 5 <= answer_length <= 25:
        score += 0.2
    elif answer_length < 5:
        score -= 0.3
    elif answer_length > 40:
        score -= 0.1
    
    # Check for academic/technical indicators
    academic_indicators = ['process', 'method', 'theory', 'principle', 'concept', 'phenomenon']
    if any(indicator in term.lower() or indicator in answer.lower() for indicator in academic_indicators):
        score += 0.15
    
    # Penalize if term appears multiple times in answer (circular definition)
    if term.lower() in answer.lower():
        score -= 0.2
    
    return max(0.1, score)

def _extract_key_concepts(text: str) -> Set[str]:
    """Extract key concepts using NLP if available, otherwise use simple heuristics"""
    concepts = set()
    
    if nlp:
        doc = nlp(text)
        # Extract noun phrases and named entities
        for chunk in doc.noun_chunks:
            if 2 <= len(chunk.text.split()) <= 4:
                concepts.add(chunk.text.title())
        
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT', 'WORK_OF_ART']:
                concepts.add(ent.text.title())
    else:
        capitalized_phrases = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
        concepts.update(capitalized_phrases)
    
    return concepts

def extract_flashcards(text: str, max_cards: int = 12, quality_threshold: float = 0.6) -> List[Dict[str, str]]:
    """Enhanced flashcard extraction with quality scoring and concept detection"""
    cards: List[Tuple[Dict[str, str], float]] = []
    seen = set()
    
    # Get key concepts for additional flashcard generation
    # key_concepts = _extract_key_concepts(text)  # TODO: Implement key concepts usage
    text_sentences = sentences(text)
    for i, s in enumerate(text_sentences):
        s_clean = normalize_space(s)
        context = " ".join(text_sentences[max(0, i-1):i+2])
        
        for pat in _DEF_PATTERNS:
            m = re.match(pat, s_clean, flags=re.IGNORECASE)
            if not m:
                continue

            term = _clean_term(m.group(1))
            ans = _clean_defn(m.group(2))

            if len(term) < 2 or len(ans) < 5:
                continue
            if len(term.split()) > 8:
                continue

            key = term.lower()
            if key in seen:
                break
            
            quality_score = _calculate_quality_score(term, ans, context)
            
            if quality_score >= quality_threshold:
                seen.add(key)
                
                q_word = "are" if re.search(r"\b(are)\b", s_clean, re.I) else "is"
                card = {
                    "term": term,
                    "question": f"What {q_word} {term}?",
                    "answer": ans,
                    "quality_score": round(quality_score, 2),
                    "source": "pattern_match"
                }
                cards.append((card, quality_score))
            break

        if len(cards) >= max_cards * 2:
            break
    
    cards.sort(key=lambda x: x[1], reverse=True)
    return [card[0] for card in cards[:max_cards]]

def generate_concept_cards(text: str, concepts: Set[str], max_cards: int = 5) -> List[Dict[str, str]]:
    """Generate additional flashcards for key concepts found in text"""
    cards = []
    # text_lower = text.lower()  # TODO: Use text_lower for case-insensitive operations
    
    for concept in list(concepts)[:max_cards]:
        concept_sentences = []
        for sentence in sentences(text):
            if concept.lower() in sentence.lower():
                concept_sentences.append(sentence)
        
        if concept_sentences:
            context = " ".join(concept_sentences[:2])
            context_clean = normalize_space(context)
            definition_match = re.search(
                rf"{re.escape(concept)}\s+(?:is|are|refers to|means)\s+([^.!?]+[.!?])",
                context_clean,
                re.IGNORECASE
            )
            
            if definition_match:
                definition = definition_match.group(1).strip()
                cards.append({
                    "term": concept,
                    "question": f"What is {concept}?",
                    "answer": definition,
                    "quality_score": 0.7,
                    "source": "concept_extraction"
                })
    
    return cards