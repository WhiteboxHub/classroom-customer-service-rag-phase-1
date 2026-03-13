"""
test_entity_extractor.py
Unit tests for EntityExtractor.

spaCy is used for real NER so these tests require the spaCy model to be
installed (en_core_web_sm). They are integration-style unit tests — fast
but need the model present.

Install: python -m spacy download en_core_web_sm
"""
import pytest


@pytest.fixture(scope="module")
def extractor():
    """Load EntityExtractor once for all tests in this module."""
    from app.services.preprocessing.entity_extractor import EntityExtractor
    return EntityExtractor()


# ── Basic extraction tests ────────────────────────────────────────────────────

def test_extract_returns_list(extractor):
    """extract() must always return a list."""
    result = extractor.extract("Hello world.")
    assert isinstance(result, list)


def test_extract_person(extractor):
    """Person entity should be detected from a clear sentence."""
    entities = extractor.extract("Alice Smith is the account manager.")
    types = [e["type"] for e in entities]
    assert "Person" in types, f"Expected Person in {entities}"


def test_extract_organization(extractor):
    """Organization entity should be detected."""
    entities = extractor.extract("She works at Kaiser Permanente.")
    types = [e["type"] for e in entities]
    assert "Organization" in types or "Location" in types, f"Expected Organization or Location in {entities}"


def test_extract_location(extractor):
    """Location entity should be detected."""
    entities = extractor.extract("The office is located in San Francisco.")
    types = [e["type"] for e in entities]
    assert "Location" in types, f"Expected Location in {entities}"


def test_extract_system_heuristic(extractor):
    """Entities containing 'system' keyword should be typed as System."""
    entities = extractor.extract("The Billing System processes all payments.")
    # May or may not be detected by NER, but if detected it must be 'System'
    billing_system_entities = [e for e in entities if "Billing" in e["entity"]]
    for ent in billing_system_entities:
        assert ent["type"] == "System", f"Expected System type for {ent}"


def test_extract_no_entities_in_empty_text(extractor):
    """Empty text should produce an empty list."""
    result = extractor.extract("")
    assert result == []


def test_extract_deduplicates(extractor):
    """Same entity mentioned twice should appear only once."""
    text = "Alice contacted Alice again to confirm."
    entities = extractor.extract(text)
    names = [e["entity"] for e in entities]
    assert names.count("Alice") <= 1, f"Duplicate entity found: {names}"


def test_extract_entity_schema(extractor):
    """Every entity in the result must have 'entity' and 'type' keys."""
    entities = extractor.extract("John called Microsoft about a billing issue.")
    for ent in entities:
        assert "entity" in ent, f"Missing 'entity' key in {ent}"
        assert "type" in ent, f"Missing 'type' key in {ent}"


def test_extract_short_tokens_excluded(extractor):
    """Entities shorter than 2 characters should be filtered out."""
    entities = extractor.extract("Go to the U.S.A. and check.")
    for ent in entities:
        assert len(ent["entity"]) >= 2, f"Short entity found: {ent}"
