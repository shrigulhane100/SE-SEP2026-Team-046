-- Supplementary PostgreSQL constraints for the Rock Starz mentoring platform.
-- Review against the existing SQLAlchemy models and migration history before applying.
-- Do not add a constraint or index again if it already exists in the schema.

-- USERS
ALTER TABLE users
ADD CONSTRAINT chk_users_role
CHECK (role IN ('STUDENT', 'MENTOR', 'ADMIN'));

-- STUDENT_PROFILES
ALTER TABLE student_profiles
ADD CONSTRAINT uq_student_profiles_user UNIQUE (user_id);

ALTER TABLE student_profiles
ADD CONSTRAINT uq_student_profiles_roll UNIQUE (roll_number);

-- MENTOR_PROFILES
ALTER TABLE mentor_profiles
ADD CONSTRAINT uq_mentor_profiles_user UNIQUE (user_id);

-- STUDENT_GUIDANCE_AREAS
-- Composite primary key: (student_profile_id, area_id).
-- Both columns should reference their respective parent tables.

-- MENTOR_GUIDANCE_AREAS
-- Composite primary key: (mentor_profile_id, area_id).
-- Both columns should reference their respective parent tables.

-- MENTORING_REQUESTS
ALTER TABLE mentoring_requests
ADD CONSTRAINT chk_mentoring_request_status
CHECK (status IN ('PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CANCELLED'));

CREATE INDEX ix_requests_student ON mentoring_requests(student_id);
CREATE INDEX ix_requests_mentor ON mentoring_requests(mentor_id);
CREATE INDEX ix_requests_status ON mentoring_requests(status);
CREATE INDEX ix_requests_expiry ON mentoring_requests(expires_at);

-- MENTORING_RELATIONSHIPS
ALTER TABLE mentoring_relationships
ADD CONSTRAINT uq_relationship_request UNIQUE (request_id);

ALTER TABLE mentoring_relationships
ADD CONSTRAINT chk_relationship_status
CHECK (status IN ('ACTIVE', 'PAUSED', 'COMPLETED', 'CLOSED'));

-- FEEDBACK
ALTER TABLE feedback
ADD CONSTRAINT chk_feedback_rating CHECK (rating BETWEEN 1 AND 5);

-- ACTIVITIES.created_by and FEEDBACK.given_by
-- These columns must reference users(user_id), as represented in the ER design.
-- Add the foreign keys through a migration if they are not already present.

-- NOTIFICATIONS
CREATE INDEX ix_notifications_user_read
ON notifications(user_id, is_read);

-- APPLICATION-LEVEL RULES (enforce in service logic and transactions)
-- 1. Create a relationship only for an ACCEPTED request.
-- 2. Accept, reject, cancel or expire requests only when the current status allows it.
-- 3. Perform request acceptance and relationship creation in one transaction.
-- 4. Validate notification reference_type/reference_id against the related entity.
-- 5. Pending requests are intended to expire after 48 hours; recheck PENDING status
--    when the expiry operation executes.