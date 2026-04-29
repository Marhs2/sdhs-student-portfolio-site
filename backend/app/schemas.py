from typing import Literal

from pydantic import BaseModel, Field, field_validator


MAX_NAME_LENGTH = 80
MAX_TEXT_LENGTH = 2000
MAX_HTML_LENGTH = 60000
MAX_URL_LENGTH = 2048
MAX_TAGS = 20
MAX_TAG_LENGTH = 40


def _validate_tags(tags: list[str] | None) -> list[str] | None:
    if tags is None:
        return None
    if len(tags) > MAX_TAGS:
        raise ValueError(f"태그는 최대 {MAX_TAGS}개까지 입력할 수 있습니다.")
    for tag in tags:
        if len(str(tag)) > MAX_TAG_LENGTH:
            raise ValueError(f"태그는 최대 {MAX_TAG_LENGTH}자까지 입력할 수 있습니다.")
    return tags


class ProfilePayload(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    description: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    job: str | None = Field(default=None, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=MAX_TAGS)
    github: str = Field(default="", max_length=MAX_URL_LENGTH)
    imageUrl: str = Field(default="", max_length=MAX_URL_LENGTH)
    isVisible: bool = True
    createProfileConsent: bool = Field(default=False, exclude=True, validate_default=True)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        return _validate_tags(value) or []

    @field_validator("createProfileConsent")
    @classmethod
    def require_create_profile_consent(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("프로필 생성 동의가 필요합니다.")
        return value


class ProfileUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_TEXT_LENGTH)
    job: str | None = Field(default=None, max_length=80)
    tags: list[str] | None = Field(default=None, max_length=MAX_TAGS)
    github: str | None = Field(default=None, max_length=MAX_URL_LENGTH)
    imageUrl: str | None = Field(default=None, max_length=MAX_URL_LENGTH)
    isVisible: bool | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None) -> list[str] | None:
        return _validate_tags(value)


class HtmlContentPayload(BaseModel):
    html: str = Field(default="", max_length=MAX_HTML_LENGTH)


class PortfolioItemPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    contribution: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    tags: list[str] = Field(default_factory=list, max_length=MAX_TAGS)
    githubUrl: str = Field(default="", max_length=MAX_URL_LENGTH)
    websiteUrl: str = Field(default="", max_length=MAX_URL_LENGTH)
    customLinkUrl: str = Field(default="", max_length=MAX_URL_LENGTH)
    videoUrl: str = Field(default="", max_length=MAX_URL_LENGTH)
    imageUrl: str = Field(default="", max_length=MAX_URL_LENGTH)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        return _validate_tags(value) or []


class PortfolioItemUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=MAX_TEXT_LENGTH)
    contribution: str | None = Field(default=None, max_length=MAX_TEXT_LENGTH)
    tags: list[str] | None = Field(default=None, max_length=MAX_TAGS)
    githubUrl: str | None = Field(default=None, max_length=MAX_URL_LENGTH)
    websiteUrl: str | None = Field(default=None, max_length=MAX_URL_LENGTH)
    customLinkUrl: str | None = Field(default=None, max_length=MAX_URL_LENGTH)
    videoUrl: str | None = Field(default=None, max_length=MAX_URL_LENGTH)
    imageUrl: str | None = Field(default=None, max_length=MAX_URL_LENGTH)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None) -> list[str] | None:
        return _validate_tags(value)


class AdminProfileUpdatePayload(BaseModel):
    featuredRank: int | None = Field(default=None, ge=1)
    reviewStatus: Literal["draft", "review", "approved", "banned"] | None = None
    isVisible: bool | None = None


class ServerAdminProfileUpdatePayload(AdminProfileUpdatePayload):
    school: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    track: str | None = Field(default=None, max_length=120)
    isAdmin: bool | None = None


class DepartmentPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class GithubCommitBatchPayload(BaseModel):
    usernames: list[str] = Field(default_factory=list, min_length=1, max_length=20)
