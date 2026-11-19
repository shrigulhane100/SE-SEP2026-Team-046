from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth import CurrentUser, Database
from app.engagement_schemas import (
    NotificationList,
    NotificationReadResult,
    NotificationResponse,
)
from app.mentoring_schemas import ResourceId
from app.models import (
    MentoringRelationship,
    MentoringRequest,
    Notification,
    NotificationReference,
    NotificationType,
)
from app.schemas import ErrorResponse

notification_router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    responses={401: {"model": ErrorResponse, "description": "Authentication required"}},
)


def notify(
    db: Session,
    recipient: int,
    event: NotificationType,
    message: str,
    reference: MentoringRequest | MentoringRelationship,
) -> None:
    if isinstance(reference, MentoringRequest):
        reference_type = NotificationReference.REQUEST
        reference_id = reference.request_id
    else:
        reference_type = NotificationReference.RELATIONSHIP
        reference_id = reference.relationship_id
    db.add(
        Notification(
            user_id=recipient,
            type=event,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
        )
    )


@notification_router.get("")
def list_notifications(user: CurrentUser, db: Database) -> NotificationList:
    items = [
        NotificationResponse.model_validate(row)
        for row in db.scalars(
            select(Notification)
            .where(Notification.user_id == user.user_id)
            .order_by(
                Notification.created_at.desc(), Notification.notification_id.desc()
            )
        )
    ]
    return NotificationList(items=items, unread=sum(not item.is_read for item in items))


@notification_router.post("/read-all")
def mark_all_read(user: CurrentUser, db: Database) -> NotificationReadResult:
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return NotificationReadResult()


@notification_router.post(
    "/{notification_id}/read",
    responses={404: {"model": ErrorResponse, "description": "Notification not found"}},
)
def mark_read(
    notification_id: ResourceId, user: CurrentUser, db: Database
) -> NotificationReadResult:
    updated = db.scalar(
        update(Notification)
        .where(
            Notification.notification_id == notification_id,
            Notification.user_id == user.user_id,
        )
        .values(is_read=True)
        .returning(Notification.notification_id)
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.commit()
    return NotificationReadResult()
