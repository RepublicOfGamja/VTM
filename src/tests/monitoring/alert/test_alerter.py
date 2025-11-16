from unittest.mock import MagicMock, patch

from vectorwave.monitoring.alert.factory import get_alerter
from vectorwave.monitoring.alert.null_alerter import NullAlerter
from vectorwave.monitoring.alert.webhook_alerter import WebhookAlerter
from vectorwave.models.db_config import WeaviateSettings

@patch('vectorwave.monitoring.alert.factory.get_weaviate_settings')
def test_get_alerter_returns_null_alerter_by_default(mock_get_settings):
    """
    Case 1: When .env settings are missing or ALERTER_STRATEGY="none"
    - Should return NullAlerter.
    """
    # 1. Arrange
    # Clear lru_cache to bypass caching
    get_alerter.cache_clear()

    # Mock default settings (strategy="none")
    mock_get_settings.return_value = WeaviateSettings()

    # 2. Act
    alerter = get_alerter()

    # 3. Assert
    assert isinstance(alerter, NullAlerter)

@patch('vectorwave.monitoring.alert.factory.get_weaviate_settings')
def test_get_alerter_returns_webhook_alerter_when_configured(mock_get_settings):
    """
    Case 2: When ALERTER_STRATEGY="webhook" and URL is provided
    - Should return WebhookAlerter.
    """
    # 1. Arrange
    get_alerter.cache_clear()

    # Mock settings object with webhook strategy and URL
    settings = WeaviateSettings(
        ALERTER_STRATEGY="webhook",
        ALERTER_WEBHOOK_URL="https://test.webhook.url/..."
    )
    mock_get_settings.return_value = settings

    # 2. Act
    alerter = get_alerter()

    # 3. Assert
    assert isinstance(alerter, WebhookAlerter)
    assert alerter.url == "https://test.webhook.url/..."

@patch('vectorwave.monitoring.alert.factory.get_weaviate_settings')
def test_get_alerter_returns_null_alerter_if_webhook_url_missing(mock_get_settings):
    """
    Case 3: When ALERTER_STRATEGY="webhook" but URL is missing
    - Should log a warning and return NullAlerter.
    """
    # 1. Arrange
    get_alerter.cache_clear()

    # Mock settings with missing URL
    settings = WeaviateSettings(
        ALERTER_STRATEGY="webhook",
        ALERTER_WEBHOOK_URL=None # URL is missing
    )
    mock_get_settings.return_value = settings

    # 2. Act
    alerter = get_alerter()

    # 3. Assert
    assert isinstance(alerter, NullAlerter)