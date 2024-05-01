import logging

from requests.exceptions import RequestException

from attrs import asdict, define, field, validators

from pers.xml_handlers import *

logger = logging.getLogger(__name__)


@define
class AuthorRecord:
    # required fields
    id: str = field()
    email_address: str = field()
    first_name: str = field()
    last_name: str = field()
    dlc: str = field()

    # optional fields
    mit_id: str = field(default=None)
    start_date: str = field(default=None)
    end_date: str = field(default=None)

    @classmethod
    def create(cls, author_data: dict):
        try:
            return cls(**author_data)
        except TypeError as exception:
            msg = f"Author with Elements ID {author_data['id']} is missing required information."
            logger.warning(msg)
            raise exception

    @classmethod
    def get_author_from_elements(cls, elements_client, author_id: str, base_url: str):
        logger.info(f"Retrieving data for author with Elements ID: {author_id}")
        author_url = f"{base_url.rstrip('/')}/users/{author_id}"
        try:
            response = elements_client.get(url=author_url)
        except RequestException as exception:
            msg = (
                f"Author with ID {author_id} not found in Elements. "
                "Please confirm the Elements ID and try again."
            )
            logger.info(msg)
            raise exception
        author_data = parse_author_xml(response.text)
        author_data["id"] = author_id
        return author_data

    def get_publications_from_elements(self, elements_client, author_id: str, base_url):
        """Get list of publications for a given author.

        A publication is considered for a request if it meets the
        preliminary set of criteria:
        """
        author_publications_url = (
            f"{base_url.rstrip('/')}/users/{author_id}/publications?&detail=full"
        )
        response = elements_client.get(url=author_publications_url)
        author_publications = parse_author_pubs_xml(response.text, asdict(self))
        msg = f"Request needed for {len(author_publications)} publication(s) by author"
        logger.info(msg)
        return author_publications


@define
class PublicationRecord:
    # publication required fields
    id: str = field(validator=validators.instance_of(str))

    # citation required fields
    _citation: str = field(alias="_citation", validator=validators.instance_of(str))
    author_first_name: str = field(validator=validators.instance_of(str))
    author_last_name: str = field(validator=validators.instance_of(str))
    title: str = field(validator=validators.instance_of(str))
    journal_name: str = field(validator=validators.instance_of(str))

    # publication fields
    doi: str = field(default=None)
    publisher: str = field(default=None)
    c_method_of_acquisition: str = field(default=None)
    c_publisher_related_email_message: str = field(default=None)
    publication_year: str = field(default=None)
    journal_elements_url: str = field(default=None)
    volume: str = field(default=None)
    issue: str = field(default=None)

    @property
    def citation(self):
        if self._citation:
            return self._citation

        _citation = "{last}, {first_init}. ".format(
            last=self.author_last_name,
            first_init=self.author_first_name[0],
        )

        if self.publication_year:
            _citation += f"({self.publication_year}). "

        _citation += "{title}. {journal}".format(
            title=self.title, journal=self.journal_name
        )

        if self.volume and self.issue:
            _citation += ", {volume}({issue})".format(
                volume=self.volume, issue=self.issue
            )

        _citation += "."

        if self.doi:
            _citation += ' <a href="https://doi.org/{doi}">doi:{doi}' "</a>".format(
                doi=self.doi
            )
        return _citation

    @classmethod
    def create(cls, publication_data: dict):
        try:
            return cls(**publication_data)
        except TypeError as exception:
            msg = f"Publication with Elements ID {publication_data['id']} is missing required information."
            logger.warning(msg)
            raise exception

    @classmethod
    def get_publication_from_elements(
        cls, elements_client, publication_id: str, base_url: str
    ):
        publication_url = f"{base_url.rstrip('/')}/publications/{publication_id}"
        response = elements_client.get(url=publication_url)
        publication_data = parse_publication_xml(response.text)
        if journal_url := publication_data["journal_elements_url"]:
            journal_policies_url = f"{journal_url}/policies?detail=full"
            policy_data = parse_journal_policies(
                elements_client.get(journal_policies_url).text
            )
            publication_data.update(policy_data)
        return publication_data

    def check_acquisition_method(self):
        if self.c_method_of_acquisition.lower() == "recruit_from_author_fpv":
            if self.doi and self.publisher:
                return True
        return False
