import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.models import MentoringRequest, NotificationType, RequestStatus
from app.notifications import notify

logger = logging.getLogger(__name__)
EXPIRY_CHECK_SECONDS = 60
EXPIRY_BATCH_SIZE = 200


def expire_pending(
    db: Session, now: datetime, *conditions, skip_locked: bool = False
) -> int:
    """Mark pending requests due at or before the supplied time as expired."""
    due = (
        select(MentoringRequest.request_id)
        .where(
            MentoringRequest.status == RequestStatus.PENDING,
            MentoringRequest.expires_at <= now,
            *conditions,
        )
        .order_by(MentoringRequest.request_id)
        .with_for_update(skip_locked=skip_locked)
    )
    if skip_locked:
        due = due.limit(EXPIRY_BATCH_SIZE)
    expired = list(
        db.scalars(
            update(MentoringRequest)
            .where(MentoringRequest.request_id.in_(due))
            .values(status=RequestStatus.EXPIRED)
            .returning(MentoringRequest)
        )
    )
    for record in expired:
        for participant in (record.student_id, record.mentor_id):
            notify(
                db,
                participant,
                NotificationType.REQUEST_EXPIRED,
                "A pending mentoring request expired after 48 hours.",
                record,
            )
    return len(expired)


def expire_batch(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as db:
        expire_pending(db, datetime.now(UTC), skip_locked=True)


async def run_expiry_worker(
    sessions: sessionmaker[Session], stop: asyncio.Event
) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=EXPIRY_CHECK_SECONDS)
        except TimeoutError:
            try:
                await asyncio.to_thread(expire_batch, sessions)
            except SQLAlchemyError:
                logger.exception("Could not expire overdue mentoring requests")
