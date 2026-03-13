"""
entity_extractor.py
Extracts named entities from text using spaCy.

Supported entity types (mapped from spaCy's NER labels):
    Person       ← PERSON
    Organization ← ORG
    Location     ← GPE, LOC
    Product      ← PRODUCT
    System       ← (rule: entities containing "system", "platform", "service", "portal")
    Concept      ← everything else noteworthy (NORP, EVENT, LAW, WORK_OF_ART, FAC)

Output format:
    [{"entity": "John", "type": "Person"}, ...]
"""
from typing import List, Dict

# Lazy-load spaCy model to avoid import-time cost
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
    return _nlp


# ── spaCy label → our canonical type ──────────────────────────────────────────
_LABEL_MAP: Dict[str, str] = {
    "PERSON": "Person",
    "ORG": "Organization",
    "GPE": "Location",
    "LOC": "Location",
    "PRODUCT": "Product",
    "NORP": "Concept",
    "EVENT": "Concept",
    "LAW": "Concept",
    "WORK_OF_ART": "Concept",
    "FAC": "Location",
}

_SYSTEM_KEYWORDS = {"system", "platform", "service", "portal", "engine", "module"}


def _classify_entity(text: str, spacy_label: str) -> str:
    """
    Return our canonical entity type for a given (text, spaCy label) pair.
    Tokens containing "System"-like words are re-classified as 'System'.
    """
    if any(kw in text.lower() for kw in _SYSTEM_KEYWORDS):
        return "System"
    return _LABEL_MAP.get(spacy_label, "Concept")


class EntityExtractor:
    """
    Extracts entities from a text chunk using spaCy NER.

    Usage:
        extractor = EntityExtractor()
        entities = extractor.extract("Alice works at Acme Corp in Boston.")
        # → [
        #     {"entity": "Alice",     "type": "Person"},
        #     {"entity": "Acme Corp", "type": "Organization"},
        #     {"entity": "Boston",    "type": "Location"},
        #   ]
    """

    def __init__(self):
        # Trigger model load on first class instantiation
        _get_nlp()

    def extract(self, text: str) -> List[Dict[str, str]]:
        """
        Extract entities from *text*.

        Args:
            text: Raw text (typically a single chunk).

        Returns:
            Deduplicated list of {"entity": <name>, "type": <canonical_type>} dicts.
            Entities shorter than 2 characters are silently skipped.
        """
        nlp = _get_nlp()
        doc = nlp(text)

        seen: set = set()
        entities: List[Dict[str, str]] = []

        for ent in doc.ents:
            name = ent.text.strip()
            if len(name) < 2:
                continue
            if name in seen:
                continue
            seen.add(name)

            entity_type = _classify_entity(name, ent.label_)
            entities.append({"entity": name, "type": entity_type})

        return entities
