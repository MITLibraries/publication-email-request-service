import logging
import sys

sys.path.append("/Users/jcuerdo/Documents/repos/publication-email-request-service")

from typing import Any

from attrs import define, field
from sqlalchemy import Engine, MetaData, create_engine, or_, select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.orm import Session

from pers.database.models import Author, DLC
from pers.record import AuthorRecord

logger = logging.getLogger(__name__)


@define
class DatabaseEngine:
    engine: Engine = field(default=None)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.engine:
            return self.engine

        nonconfigured_engine_error_message = (
            "No SQLAlchemy engine was found. The engine must be created "
            "by running 'engine.configure()' with a valid connection string."
        )
        raise AttributeError(nonconfigured_engine_error_message)

    @classmethod
    def configure(cls, connection_string: str) -> None:
        return cls(engine=create_engine(connection_string))

    def init_db(self, metadata: MetaData):
        """Initialize database using provided metadata.

        This command will emit CREATE TABLE statements, or DDL, to the database.

        Args:
            metadata (MetaData): A collection of Table objects (or ORM classes) and
                their associated schema constructs.
        """
        metadata.create_all(self.engine)

    def create(self, record):
        if isinstance(record, AuthorRecord):
            self._upsert_author(record)

    def _upsert_author(self, record):
        dlc = DLC(name=record.dlc)
        author = Author(
            id=record.id,
            email_address=record.email_address,
            first_name=record.first_name,
            last_name=record.last_name,
        )

        with Session(self.engine) as session:
            dlc_upsert_stmt = sqlite_upsert(DLC).values([dlc.to_dict()])
            logger.info(f"DLC upsert")
            session.execute(
                dlc_upsert_stmt.on_conflict_do_nothing(index_elements=[DLC.name])
            )
            logger.info(f"Author upsert")
            author_upsert_statement = sqlite_upsert(Author).values([author.to_dict()])
            session.execute(
                author_upsert_statement.on_conflict_do_update(
                    index_elements=[Author.id], set_=author.to_dict()
                )
            )
            # THIS DOESN'T WORK
            dlc.authors.append(author)
            session.commit()


if __name__ == "__main__":
    from sqlalchemy import select
    from pers.database.models import Author, Email, Publication, DLC

    CONNECTION_STRING = "sqlite:///foo.db"
    engine = DatabaseEngine.configure(CONNECTION_STRING)

    with Session(engine()) as session:
        result = session.execute(select(DLC))
        print(session.execute(select(DLC)).all())
        print(session.execute(select(Author)).all())
