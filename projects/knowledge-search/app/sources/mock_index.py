"""Mock corpus: Notion + Slack + Drive docs."""
from __future__ import annotations

from app.models import Document

DOCS: list[Document] = [
    Document(
        id="notion-refund-policy",
        source="notion",
        title="Refund Policy (2026)",
        body="Customers may request one full refund within 14 days of purchase. "
        "Annual plans: prorated refund if cancelled within 30 days. "
        "Enterprise: custom terms in MSA. Escalate repeat refunders to finance.",
        url="https://notion.so/refund-policy",
        updated_at="2026-05-01",
    ),
    Document(
        id="notion-onboarding",
        source="notion",
        title="Customer Onboarding Playbook",
        body="Week 1: integration setup call. Week 2: first value milestone. "
        "Send checklist after signup. CSM owns accounts over $500 MRR.",
        url="https://notion.so/onboarding",
        updated_at="2026-04-12",
    ),
    Document(
        id="slack-eng-incident",
        source="slack",
        title="#incidents — API outage 2026-06-10",
        body="Postmortem: Stripe webhook delay caused duplicate charges for 47 customers. "
        "Fix deployed. Support macro: acknowledge + refund if duplicate confirmed.",
        url="https://slack.com/archives/incidents/p123",
        updated_at="2026-06-11",
    ),
    Document(
        id="drive-msa-template",
        source="drive",
        title="Enterprise MSA Template v3",
        body="SLA: 99.9% uptime. Data retention 90 days. SOC2 report available on request. "
        "Support tier: dedicated CSM for $2k+ MRR.",
        url="https://drive.google.com/msa-v3",
        updated_at="2026-03-20",
    ),
    Document(
        id="notion-churn-playbook",
        source="notion",
        title="Churn Save Playbook",
        body="At-risk signals: failed payment, 14d inactive, 3+ support tickets. "
        "Offer discount or onboarding reset. Loop in product if integration stall.",
        url="https://notion.so/churn-save",
        updated_at="2026-06-01",
    ),
]


def all_documents() -> list[Document]:
    return list(DOCS)
