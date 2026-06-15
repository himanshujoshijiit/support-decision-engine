"""Customer-context providers (billing + helpdesk history)."""

from app.config import get_settings
from app.context.base import ContextProvider
from app.context.mock_provider import MockContextProvider


def get_context_provider() -> ContextProvider:
    """Factory: pick a provider based on configuration."""
    settings = get_settings()
    if settings.context_provider == "stripe":
        # Imported lazily so the `stripe` package is only required when used.
        from app.context.stripe_provider import StripeContextProvider

        return StripeContextProvider(api_key=settings.stripe_api_key)
    return MockContextProvider()
