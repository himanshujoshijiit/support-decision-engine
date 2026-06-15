"""Knowledge search tests."""
from app.search.engine import search


def test_refund_policy_found():
    hits = search("refund policy annual")
    assert hits
    assert any("refund" in h.document.title.lower() for h in hits)
