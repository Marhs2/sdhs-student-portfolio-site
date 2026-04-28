import pytest
from pydantic import ValidationError

from backend.app.schemas import (
    HtmlContentPayload,
    PortfolioItemPayload,
    ProfilePayload,
)


def test_profile_payload_rejects_oversized_text() -> None:
    with pytest.raises(ValidationError):
        ProfilePayload(
            name="Student",
            description="x" * 2001,
            createProfileConsent=True,
        )


def test_html_payload_rejects_oversized_html() -> None:
    with pytest.raises(ValidationError):
        HtmlContentPayload(html="x" * 60001)


def test_portfolio_payload_rejects_too_many_tags() -> None:
    with pytest.raises(ValidationError):
        PortfolioItemPayload(
            title="Project",
            tags=[f"tag-{index}" for index in range(21)],
        )
