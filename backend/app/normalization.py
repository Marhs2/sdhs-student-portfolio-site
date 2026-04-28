import re
from html import escape, unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse


JOB_LABELS = [
    "프론트엔드",
    "백엔드",
    "풀스택",
    "그래픽",
    "게임 개발",
    "AI",
    "데이터 분석",
    "모바일 앱",
    "임베디드",
    "사이버 보안",
    "UI/UX",
    "기획",
    "영상",
]


def _normalize_key(value: str) -> str:
    return re.sub(r"[\s\-_]+", "", value or "").casefold()


JOB_ALIASES = {
    _normalize_key("프론트엔드"): "프론트엔드",
    _normalize_key("프론트 엔드 개발자"): "프론트엔드",
    _normalize_key("프론트엔드 개발자"): "프론트엔드",
    _normalize_key("frontenddeveloper"): "프론트엔드",
    _normalize_key("frontend"): "프론트엔드",
    _normalize_key("?꾨줎???붾뱶 媛쒕컻??"): "프론트엔드",
    _normalize_key("백엔드"): "백엔드",
    _normalize_key("백 엔드 개발자"): "백엔드",
    _normalize_key("백엔드 개발자"): "백엔드",
    _normalize_key("backenddeveloper"): "백엔드",
    _normalize_key("backend"): "백엔드",
    _normalize_key("諛??붾뱶 媛쒕컻??"): "백엔드",
    _normalize_key("풀스택"): "풀스택",
    _normalize_key("풀 스택 개발자"): "풀스택",
    _normalize_key("풀스택 개발자"): "풀스택",
    _normalize_key("fullstackdeveloper"): "풀스택",
    _normalize_key("fullstack"): "풀스택",
    _normalize_key("? ?ㅽ깮 媛쒕컻??"): "풀스택",
    _normalize_key("그래픽"): "그래픽",
    _normalize_key("graphicsdesigner"): "그래픽",
    _normalize_key("graphicdesigner"): "그래픽",
    _normalize_key("洹몃옒??"): "그래픽",
    _normalize_key("게임 개발"): "게임 개발",
    _normalize_key("게임 개발자"): "게임 개발",
    _normalize_key("gamedeveloper"): "게임 개발",
    _normalize_key("game"): "게임 개발",
    _normalize_key("寃뚯엫 媛쒕컻??"): "게임 개발",
    _normalize_key("ai"): "AI",
    _normalize_key("artificialintelligence"): "AI",
    _normalize_key("데이터분석"): "데이터 분석",
    _normalize_key("dataanalytics"): "데이터 분석",
    _normalize_key("dataanalyst"): "데이터 분석",
    _normalize_key("mobile"): "모바일 앱",
    _normalize_key("mobileapp"): "모바일 앱",
    _normalize_key("appdeveloper"): "모바일 앱",
    _normalize_key("embedded"): "임베디드",
    _normalize_key("iot"): "임베디드",
    _normalize_key("security"): "사이버 보안",
    _normalize_key("cybersecurity"): "사이버 보안",
    _normalize_key("uiux"): "UI/UX",
    _normalize_key("designer"): "UI/UX",
    _normalize_key("planning"): "기획",
    _normalize_key("pm"): "기획",
    _normalize_key("video"): "영상",
    _normalize_key("motion"): "영상",
}

ALLOWED_HTML_TAGS = {
    "a",
    "blockquote",
    "br",
    "code",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "section",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
}
VOID_HTML_TAGS = {"br"}
DROP_CONTENT_TAGS = {
    "applet",
    "base",
    "button",
    "embed",
    "form",
    "iframe",
    "input",
    "link",
    "meta",
    "object",
    "script",
    "select",
    "style",
    "textarea",
}
ALLOWED_HTML_ATTRIBUTES = {
    "a": {"href", "title"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}


def normalize_job(value: str | None) -> str | None:
    if not value:
        return None

    stripped = value.strip()
    return JOB_ALIASES.get(_normalize_key(stripped), stripped)


def _clean_html_url(value: str | None) -> str:
    decoded = unescape(value or "")
    normalized = re.sub(r"[\x00-\x20\x7f]+", "", decoded).strip()
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return normalized


def _clean_html_span(value: str | None, *, max_length: int = 12) -> str:
    normalized = str(value or "").strip()
    if not normalized.isdigit():
        return ""
    return normalized[:max_length]


class RichHtmlSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.drop_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in DROP_CONTENT_TAGS:
            self.drop_depth += 1
            return
        if self.drop_depth or normalized_tag not in ALLOWED_HTML_TAGS:
            return

        cleaned_attrs = self._clean_attrs(normalized_tag, attrs)
        attr_text = "".join(
            f' {name}="{escape(value, quote=True)}"'
            for name, value in cleaned_attrs
        )
        self.parts.append(f"<{normalized_tag}{attr_text}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_HTML_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in DROP_CONTENT_TAGS and self.drop_depth:
            self.drop_depth -= 1
            return
        if self.drop_depth or normalized_tag not in ALLOWED_HTML_TAGS or normalized_tag in VOID_HTML_TAGS:
            return
        self.parts.append(f"</{normalized_tag}>")

    def handle_data(self, data: str) -> None:
        if not self.drop_depth:
            self.parts.append(escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")

    def _clean_attrs(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> list[tuple[str, str]]:
        allowed = ALLOWED_HTML_ATTRIBUTES.get(tag, set())
        cleaned: list[tuple[str, str]] = []
        for raw_name, raw_value in attrs:
            name = raw_name.lower()
            if name not in allowed:
                continue
            if tag == "a" and name == "href":
                href = _clean_html_url(raw_value)
                if href:
                    cleaned.extend(
                        [
                            ("href", href),
                            ("target", "_blank"),
                            ("rel", "noopener noreferrer nofollow"),
                        ]
                    )
                continue
            if name in {"colspan", "rowspan"}:
                span = _clean_html_span(raw_value)
                if span:
                    cleaned.append((name, span))
                continue
            value = str(raw_value or "").strip()
            if value:
                cleaned.append((name, value[:160]))
        return cleaned


def clean_rich_html(value: str | None) -> str:
    if not value:
        return ""

    sanitizer = RichHtmlSanitizer()
    sanitizer.feed(value.strip())
    sanitizer.close()
    return "".join(sanitizer.parts).strip()


def clean_http_url(value: str | None) -> str:
    url = (value or "").strip()
    if not url:
        return ""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return url


def clean_github_url(value: str | None) -> str:
    url = clean_http_url(value)
    if not url:
        return ""

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if hostname.lower() not in {"github.com", "www.github.com"}:
        return ""
    return url


def clean_youtube_url(value: str | None) -> str:
    url = clean_http_url(value)
    if not url:
        return ""

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        return url
    return ""


def _normalize_tag_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        tags = [value]
    elif isinstance(value, (list, tuple, set)):
        tags = list(value)
    else:
        tags = [value]

    normalized: list[str] = []
    for item in tags:
        tag = str(item).strip()
        if tag:
            normalized.append(tag)
    return normalized


def _normalize_review_status(value: Any) -> str:
    status = str(value or "").strip()
    return status or "approved"


def _normalize_visibility(value: Any) -> bool:
    return value is not False


def normalize_profile_record(
    record: dict[str, Any] | None,
    *,
    include_private: bool = False,
) -> dict[str, Any] | None:
    if not record:
        return None

    normalized = {
        "id": record.get("id"),
        "name": (record.get("name") or "").strip(),
        "description": (record.get("des") or record.get("description") or "").strip(),
        "job": normalize_job(record.get("job")),
        "school": (record.get("school") or "").strip(),
        "department": (record.get("department") or "").strip(),
        "track": (record.get("track") or "").strip(),
        "tags": _normalize_tag_list(record.get("tags")),
        "featuredRank": int(record.get("featured_rank") or 9999),
        "reviewStatus": _normalize_review_status(record.get("review_status")),
        "isVisible": _normalize_visibility(record.get("is_visible")),
        "github": clean_github_url(record.get("GITHUB") or record.get("github")),
        "imageUrl": clean_http_url(record.get("img") or record.get("imageUrl")),
        "createdAt": record.get("created_at"),
        "isAdmin": bool(record.get("isAdmin")),
    }
    if include_private:
        normalized["email"] = (record.get("email") or "").strip()
    return normalized


def normalize_portfolio_item_record(
    record: dict[str, Any] | None,
    *,
    include_private: bool = False,
) -> dict[str, Any] | None:
    if not record:
        return None

    normalized = {
        "id": record.get("id"),
        "title": (record.get("title") or "").strip(),
        "description": (record.get("des") or record.get("description") or "").strip(),
        "contribution": (record.get("project_role") or record.get("contribution") or "").strip(),
        "tags": _normalize_tag_list(record.get("skill_tags") or record.get("tags")),
        "isFeatured": bool(record.get("is_featured", False)),
        "githubUrl": clean_github_url(record.get("github_link") or record.get("githubUrl")),
        "websiteUrl": clean_http_url(
            record.get("custom_link_url")
            or record.get("websiteUrl")
            or record.get("customLinkUrl")
        ),
        "videoUrl": clean_youtube_url(record.get("youtube_link") or record.get("videoUrl")),
        "imageUrl": clean_http_url(record.get("img") or record.get("imageUrl")),
        "createdAt": record.get("created_at"),
    }
    if include_private:
        normalized["ownerEmail"] = (record.get("owner") or record.get("ownerEmail") or "").strip()
    return normalized
