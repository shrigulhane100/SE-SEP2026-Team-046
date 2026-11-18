import argparse
from getpass import getpass

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import DatabaseSettings
from app.db import create_db_engine
from app.models import User, UserRole
from app.schemas import DisplayName, EmailAddress
from app.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Rock Starz administrator.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    try:
        name = TypeAdapter(DisplayName).validate_python(args.name)
        email = TypeAdapter(EmailAddress).validate_python(args.email)
    except ValidationError:
        parser.error("Enter a valid name and email address.")

    password = getpass("Administrator password: ")
    if not 8 <= len(password) <= 128:
        parser.error("The password must have 8 to 128 characters.")
    if password != getpass("Confirm password: "):
        parser.error("The passwords do not match.")

    engine = create_db_engine(DatabaseSettings())
    try:
        with Session(engine) as db:
            if (
                db.scalar(select(User.user_id).where(func.lower(User.email) == email))
                is not None
            ):
                parser.exit(1, "An account with this email already exists.\n")

            db.add(
                User(
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    role=UserRole.ADMIN,
                )
            )
            try:
                db.commit()
            except IntegrityError as error:
                if error.orig.diag.constraint_name == "uq_users_email":
                    parser.exit(1, "An account with this email already exists.\n")
                raise
    finally:
        engine.dispose()
    print(f"Administrator created for {email}.")


if __name__ == "__main__":
    main()
