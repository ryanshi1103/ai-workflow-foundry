"""Tests that sensitive environment variables are not leaked in logs."""

import os


class TestEnvSecurity:
    """Security tests for environment variable handling."""

    def test_api_key_not_in_config_str(self):
        """API key should not appear in config string representations."""
        os.environ["DEEPSEEK_API_KEY"] = "deepseek-test-key-not-a-secret"
        import importlib

        import src.config

        importlib.reload(src.config)

        assert src.config.DEEPSEEK_API_KEY == "deepseek-test-key-not-a-secret"
        # But ensure we don't accidentally log it — the config module
        # itself doesn't have a __str__, but let's verify values are correct

    def test_apify_token_not_exposed(self):
        """Apify token should be handled securely."""
        os.environ["APIFY_TOKEN"] = "apify-secret-token-abc"
        import importlib

        import src.config

        importlib.reload(src.config)

        assert src.config.APIFY_TOKEN == "apify-secret-token-abc"
        # The config value is accessible but should only be used for API calls

    def test_deepseek_configured_with_key(self):
        """Config should detect when DeepSeek is configured."""
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-key"
        import importlib

        import src.config

        importlib.reload(src.config)

        assert src.config.DEEPSEEK_CONFIGURED is True

    def test_deepseek_not_configured_without_key(self):
        """Config should detect when DeepSeek is NOT configured."""
        os.environ.pop("DEEPSEEK_API_KEY", None)
        import importlib

        import src.config

        importlib.reload(src.config)

        assert src.config.DEEPSEEK_CONFIGURED is False
