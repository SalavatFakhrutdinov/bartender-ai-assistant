"""Smoke tests for shared package imports."""


def test_version():
    from shared import __version__

    assert __version__ == "0.1.0"


def test_settings_load():
    from shared.config import get_settings

    settings = get_settings()
    assert settings.env == "development"


def test_base_model():
    from shared.models.base import Base

    assert Base is not None
