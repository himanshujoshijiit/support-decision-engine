"""Provider interface for fetching customer context.

This abstraction is the seam that lets us ship with mocks today and plug in
Stripe / Chargebee / Zendesk for a pilot customer without touching the pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import CustomerContext


class ContextProvider(ABC):
    """Fetches the billing + history context for a customer."""

    @abstractmethod
    def fetch(self, customer_id: str) -> CustomerContext:
        """Return everything we know about a customer.

        Implementations should be resilient: on a partial/failed upstream lookup,
        return whatever context is available rather than raising, so the engine can
        still make a (lower-confidence) call.
        """
        raise NotImplementedError
