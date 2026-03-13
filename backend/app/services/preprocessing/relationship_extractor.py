"""
relationship_extractor.py
Extracts relationships between entities using spaCy dependency parsing.

Algorithm:
  1. Find all entity spans in the doc.
  2. For each VERB token, look left and right in its subtree for entity spans.
  3. Yield (subject_entity) -[VERB]-> (object_entity) triples.

Output format:
    [{"source": "Customer", "relation": "CONTACTED", "target": "Support"}, ...]

Relations are upper-cased and space-replaced with underscores so they can be
used directly as Neo4j relationship types.
"""
import re
from typing import List, Dict, Set, Tuple

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


RELATION_MAP: Dict[str, str] = {
    "contact": "CONTACTED",
    "use": "USES",
    "have": "HAS",
    "contain": "CONTAINS",
    "include": "INCLUDES",
    "require": "REQUIRES",
}

def _clean_relation(lemma: str) -> str:
    """Normalise a verb lemma into a Neo4j-safe relationship type string."""
    lower_lemma = lemma.lower()
    if lower_lemma in RELATION_MAP:
        return RELATION_MAP[lower_lemma]
    
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", lemma.upper())
    return cleaned.strip("_") or "RELATED_TO"


class RelationshipExtractor:
    """
    Extracts (source, relation, target) triples from text by combining
    spaCy NER + dependency parsing.

    Usage:
        extractor = RelationshipExtractor()
        entities = [{"entity": "Customer", "type": "Person"},
                    {"entity": "Support",  "type": "System"}]
        rels = extractor.extract(
            "Customer contacted support regarding billing issue",
            entities,
        )
        # → [{"source": "Customer", "relation": "CONTACT", "target": "support"}]
    """

    def __init__(self):
        _get_nlp()

    # ── public API ─────────────────────────────────────────────────────────────

    def extract(
        self,
        text: str,
        entities: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """
        Extract relationships from *text* given the list of *entities*.

        Args:
            text:     Raw text chunk.
            entities: Output of EntityExtractor.extract() — list of
                      {"entity": <name>, "type": <type>} dicts.

        Returns:
            List of {"source": str, "relation": str, "target": str} dicts.
            Empty list if fewer than 2 entities are found.
        """
        if len(entities) < 2:
            return []

        nlp = _get_nlp()
        doc = nlp(text)

        # Build a set of known entity surface forms (lower-cased for matching)
        entity_names: Set[str] = {e["entity"].lower() for e in entities}

        relationships: List[Dict[str, str]] = []
        seen: Set[Tuple[str, str, str]] = set()

        for token in doc:
            if token.pos_ != "VERB":
                continue

            # Collect entity-like tokens in the verb's subtree
            subtree_tokens = list(token.subtree)
            subjects = self._find_entities_in_span(subtree_tokens, entity_names, {"nsubj", "nsubjpass"})
            objects = self._find_entities_in_span(subtree_tokens, entity_names, {"dobj", "pobj", "attr", "nsubjpass"})

            relation = _clean_relation(token.lemma_)

            for src in subjects:
                for tgt in objects:
                    if src == tgt:
                        continue
                    triple = (src, relation, tgt)
                    if triple not in seen:
                        seen.add(triple)
                        relationships.append(
                            {"source": src, "relation": relation, "target": tgt}
                        )

        # Fallback: if dependency parsing found nothing, create pairwise
        # CO_OCCURRENCE links between all entities in the chunk.
        if not relationships:
            relationships = self._cooccurrence_fallback(entities)

        return relationships

    # ── helpers ────────────────────────────────────────────────────────────────

    def _find_entities_in_span(
        self,
        tokens,
        entity_names: Set[str],
        dep_filter: Set[str],
    ) -> List[str]:
        """Return surface forms of tokens that match known entities and deps."""
        found = []
        for tok in tokens:
            if tok.dep_ in dep_filter and tok.text.lower() in entity_names:
                found.append(tok.text)
        return found

    def _cooccurrence_fallback(
        self,
        entities: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """
        When no verb-based triple is found, create CO_OCCURS_WITH edges
        between every unique pair of entities as a minimum graph signal.
        """
        rels = []
        names = [e["entity"] for e in entities]
        for i, src in enumerate(names):
            for tgt in names[i + 1 :]:
                rels.append({"source": src, "relation": "CO_OCCURS_WITH", "target": tgt})
        return rels
