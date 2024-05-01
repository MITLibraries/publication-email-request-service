"""Data models defined in SQLAlchemy ORM"""

from __future__ import annotations
from datetime import date

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase):
    def to_dict(self):
        return {field.name: getattr(self, field.name) for field in self.__table__.c}


####################
# association tables
####################
"""Many-to-many relationships in SQLAlchemy require intermediary tables
to connect the related tables. The intermediary table contains foreign keys
that point to the primary keys of the related tables.
"""
publications_authors_assoc = Table(
    "publication_authors_association",
    Base.metadata,
    Column("author_id", ForeignKey("author.id"), primary_key=True),
    Column("publication_id", ForeignKey("publication.id"), primary_key=True),
)


# class PublicationAuthor(Base):
#     __tablename__ = "publication_author_association"
#     publication_id = mapped_column(ForeignKey("publication.id"), primary_key=True)
#     author_id = mapped_column(ForeignKey("author.id"), primary_key=True)
#     publication = relationship("Publication", back_populates="authors")
#     author = relationship("Author", back_populates="publications")


###############
# main tables
###############


class Publication(Base):
    """Publication table.

    This table keeps track of the publications requested from authors
    when the Importer is run.
    """

    __tablename__ = "publication"
    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    citation: Mapped[str]
    email_id: Mapped[int] = mapped_column(ForeignKey("email.id"), nullable=True)
    email: Mapped["Email"] = relationship(back_populates="publications")
    authors: Mapped[list["Author"]] = relationship(
        secondary=publications_authors_assoc,
        back_populates="publications",
    )


class Email(Base):
    __tablename__ = "email"
    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("author.id"))
    author: Mapped["Author"] = relationship(back_populates="emails")
    liaison_id: Mapped[int] = mapped_column(ForeignKey("liaison.id"))
    liaison: Mapped["Liaison"] = relationship(back_populates="emails")
    publications: Mapped[list["Publication"]] = relationship(back_populates="email")
    date_sent: Mapped[date] = mapped_column(default=None, nullable=True)


##########
# people
##########
class DLC(Base):
    __tablename__ = "dlc"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    liaison_id: Mapped[int | None] = mapped_column(ForeignKey("liaison.id"))
    liaison: Mapped[Liaison | None] = relationship(back_populates="dlcs")
    authors: Mapped[list[Author]] = relationship(back_populates="dlc")


class Liaison(Base):
    __tablename__ = "liaison"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    email_address: Mapped[str]
    dlcs: Mapped[list["DLC"]] = relationship(back_populates="liaison")
    emails: Mapped[list["Email"]] = relationship(back_populates="liaison")
    active: Mapped[bool] = mapped_column(default=True)


class Author(Base):
    __tablename__ = "author"
    id: Mapped[str] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    dlc_id: Mapped[int] = mapped_column(ForeignKey("dlc.id"), nullable=True)
    dlc: Mapped["DLC"] = relationship(back_populates="authors")
    emails: Mapped[list["Email"]] = relationship(back_populates="author")
    publications: Mapped[list["Publication"]] = relationship(
        secondary=publications_authors_assoc,
        back_populates="authors",
    )
