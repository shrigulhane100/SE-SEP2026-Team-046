from sqlalchemy import func, select

from app.models import MentoringRelationship, MentoringRequest, RelationshipStatus

OPEN_RELATIONSHIP_STATUSES = (RelationshipStatus.ACTIVE, RelationshipStatus.PAUSED)


def occupied_mentees(mentor_id):
    return (
        select(func.count())
        .select_from(MentoringRelationship)
        .join(MentoringRequest)
        .where(
            MentoringRequest.mentor_id == mentor_id,
            MentoringRelationship.status.in_(OPEN_RELATIONSHIP_STATUSES),
        )
    )
