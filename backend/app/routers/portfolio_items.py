from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..auth import get_current_profile, require_portfolio_item_write_access
from ..config import get_settings
from ..repositories import (
    create_portfolio_item,
    delete_portfolio_item,
    get_profile_by_email,
    get_portfolio_item_by_id,
    is_public_approved_profile,
    list_portfolio_items,
    update_portfolio_item,
)
from ..schemas import PortfolioItemPayload, PortfolioItemUpdatePayload
from ..security_logging import log_security_event


router = APIRouter(prefix="/api/portfolio-items", tags=["portfolio-items"])


@router.get("")
def get_all_portfolio_items(response: Response) -> list[dict[str, Any]]:
    response.headers["Cache-Control"] = get_settings().public_cache_control_header
    return list_portfolio_items()


@router.get("/{item_id}")
def get_portfolio_item(item_id: int) -> dict[str, Any]:
    item = get_portfolio_item_by_id(item_id, include_private=True)
    owner_profile = get_profile_by_email(item.get("ownerEmail", ""), include_private=True) if item else None
    if not item or not is_public_approved_profile(owner_profile):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="포트폴리오 항목을 찾을 수 없습니다.",
        )
    item = dict(item)
    item.pop("ownerEmail", None)
    return item


@router.post("", status_code=status.HTTP_201_CREATED)
def post_portfolio_item(
    payload: PortfolioItemPayload,
    profile: dict = Depends(get_current_profile),
) -> dict[str, Any]:
    created = create_portfolio_item(profile["email"], payload.model_dump())
    log_security_event(
        "portfolio_item.created",
        outcome="allowed",
        actor_email=profile.get("email"),
        actor_profile_id=profile.get("id"),
        target_type="portfolio_item",
        target_id=created.get("id"),
    )
    return created


@router.put("/{item_id}")
def put_portfolio_item(
    item_id: int,
    payload: PortfolioItemUpdatePayload,
    profile: dict = Depends(require_portfolio_item_write_access),
) -> dict[str, Any]:
    update_payload = payload.model_dump(exclude_unset=True)
    updated = update_portfolio_item(item_id, update_payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="포트폴리오 항목을 찾을 수 없습니다.",
        )
    log_security_event(
        "portfolio_item.updated",
        outcome="allowed",
        actor_email=profile.get("email"),
        actor_profile_id=profile.get("id"),
        target_type="portfolio_item",
        target_id=item_id,
        changed_fields=sorted(update_payload.keys()),
    )
    return updated


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item_route(
    item_id: int,
    profile: dict = Depends(require_portfolio_item_write_access),
) -> None:
    deleted = delete_portfolio_item(item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="포트폴리오 항목을 찾을 수 없습니다.",
        )
    log_security_event(
        "portfolio_item.deleted",
        outcome="allowed",
        actor_email=profile.get("email"),
        actor_profile_id=profile.get("id"),
        target_type="portfolio_item",
        target_id=item_id,
    )
