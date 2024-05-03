from sqlalchemy import select
from sqlalchemy.orm import Session

from pers.config import Config
from pers.database.models import *
from pers.database_engine import DatabaseEngine
from pers.record import *

####################
# Prerequisites
####################
CONFIG = Config()
db_engine: DatabaseEngine = DatabaseEngine.configure(
    CONFIG.PERS_DATABASE_CONNECTION_STRING
)
db_engine.init_db(Base.metadata)  # COMMENT OUT THIS LINE IF DATABASE ALREADY EXISTS)

#######################################
# Create a test AuthorRecords
#######################################
author_record_a = AuthorRecord(
    id="001",
    email_address="bilbo.baggins@gmail.com",
    first_name="Bilbo",
    last_name="Baggins",
    dlc="Shire",
)
author_record_a_updated = AuthorRecord(
    id="001",
    email_address="bilbo.baggins@gmail.com",
    first_name="Bilbo",
    last_name="Boggins",
    dlc="Undying Lands",
)

author_record_a_updated_2 = AuthorRecord(
    id="001",
    email_address="bilbo.baggins@gmail.com",
    first_name="Bilbo",
    last_name="Boggins",
    dlc="undying Lands",
)

author_record_b = AuthorRecord(
    id="002",
    email_address="faramir@gmail.com",
    first_name="Faramir",
    last_name="Smith",
    dlc="Gondor",
)
author_record_c = AuthorRecord(
    id="003",
    email_address="samwise.gamgee@gmail.com",
    first_name="Samwise",
    last_name="Gamgee",
    dlc="Shire",
)


# Check records in each table
def check_db():
    with Session(db_engine()) as session:
        print("===================================")
        print(f"DLC Authors: {(session.scalars(select(DLC)).all())}")
        print(f"DLC Authors #: {len((session.scalars(select(DLC)).first()).authors)}")
        print(f"Author: {session.execute(select(Author)).all()}")


if __name__ == "__main__":
    # 1. Create first instance of 'author_record_a'
    db_engine.create(author_record_a)
    check_db()

    # 2. Upsert new data to instance of 'author_record_a'
    #    - Changes: last_name ("Baggins" -> "Boggins"), dlc ("Shire" -> "Undying Lands")
    db_engine.create(author_record_a_updated)
    check_db()

    # 3. Upsert new data to instance of 'author_record_a'
    #    - Changes: dlc ("Undying Lands" -> "undying Lands")
    #    - Note:
    #       - Does change letter casing of DLC record result in a new entry in 'dlc' table?: Yes
    db_engine.create(author_record_a_updated_2)
    check_db()
