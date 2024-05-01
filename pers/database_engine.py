from typing import Any

from attrs import define, field
from sqlalchemy import Engine, MetaData, create_engine, or_
from sqlalchemy.orm import Session


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
        with Session(self.engine) as session:
            session.add(record)
            session.commit()

    def get_or_create(self, record, *args):
        model = record.__class__
        with Session(self.engine) as session:
            instance = session.query(model).filter(or_(*args)).first()
            if instance:
                return instance
            else:
                session.add(record)
                session.commit()
                return record