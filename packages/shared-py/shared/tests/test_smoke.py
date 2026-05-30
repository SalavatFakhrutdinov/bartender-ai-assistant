"""Smoke tests for shared package imports."""

import pytest


def test_version():
    from shared import __version__

    assert __version__ == "0.1.0"


def test_settings_load():
    from shared.config import get_settings

    settings = get_settings()
    assert settings.env == "development"


def test_guardrail():
    from shared.models.chat import GuardrailResult

    result = GuardrailResult(allowed=True, score=1.0)
    assert result.allowed is True
