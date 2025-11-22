from functools import lru_cache
from ...models.db_config import get_weaviate_settings
from .base import BaseAlerter
from .webhook_alerter import WebhookAlerter
from .null_alerter import NullAlerter
import logging

logger = logging.getLogger(__name__)

@lru_cache()
def get_alerter() -> BaseAlerter:
    settings = get_weaviate_settings()
    strategy = settings.ALERTER_STRATEGY.lower()

    if strategy == "webhook":
        if not settings.ALERTER_WEBHOOK_URL:
            logger.warning("ALERTER_STRATEGY='webhook' but ALERTER_WEBHOOK_URL is not set. Using 'none'.")
            return NullAlerter()
        return WebhookAlerter(url=settings.ALERTER_WEBHOOK_URL)

    return NullAlerter()