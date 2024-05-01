import logging
from attrs import asdict, define

from sqlalchemy import select
from sqlalchemy.orm import Session


from pers.database.models import Author, DLC, Email, Publication
from pers.database_engine import DatabaseEngine
from pers.elements import ElementsClient
from pers.record import AuthorRecord, PublicationRecord

logger = logging.getLogger(__name__)


@define
class Importer:
    db_engine: DatabaseEngine
    elements_client: ElementsClient
    base_url: str

    def run(self, author_id: str):
        author_data = AuthorRecord.get_author_from_elements(
            self.elements_client, author_id, self.base_url
        )
        author_record = AuthorRecord.create(author_data)

        # add record to 'DLC'
        dlc = self.db_engine.get_or_create(
            DLC(name=author_record.dlc), DLC.name == author_record.dlc
        )

        # add record to 'Author' db
        author = Author(
            id=author_record.id,
            email_address=author_record.email_address,
            first_name=author_record.first_name,
            last_name=author_record.last_name,
            dlc=dlc,
        )
        self.db_engine.create(author)

        for _publication in author_record.get_publications_from_elements(
            self.elements_client, author_id, self.base_url
        ):
            publication_id = _publication["id"]
            publication_data = PublicationRecord.get_publication_from_elements(
                self.elements_client, publication_id, self.base_url
            )
            publication_data.update(
                {
                    "author_first_name": author_record.first_name,
                    "author_last_name": author_record.last_name,
                }
            )
            publication_record = PublicationRecord.create(publication_data)

            # run checks on publication
            # if self.check_if_email_request_sent(publication_id):
            #     message = (
            #         f"Publication {publication_id} already requested, skipping import"
            #     )
            #     logger.info(message)
            #     continue
            # if not publication_record.check_acquisition_method():
            #     message = f"Publication {publication_id} acquisition method ('{publication_record.c_method_of_acquisition}') is not valid, skipping import"
            #     logger.warning(message)
            #     continue

            # add record to 'Publication' db
            publication = Publication(
                id=publication_record.id,
                title=publication_record.title,
                citation=publication_record.citation,
                authors=[author],
            )
            self.db_engine.create(publication)
            logger.info(f"Finished importing publication: {publication_id}")

    def check_if_email_request_sent(self, publication_id):
        with Session(self.db_engine()) as session:
            email_id = session.scalars(
                select(Publication.email_id).where(Publication.id == publication_id)
            ).first()
            if result := session.execute(
                select(Email)
                .where(Email.id == email_id)
                .where(Email.date_sent.is_not(None))
            ).all():
                message = f"Found {len(result)} email(s) for publication {publication_id}"
                logger.debug(message)
                return True
            return False
