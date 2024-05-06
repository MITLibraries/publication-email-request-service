import logging
import requests

from attrs import define, field
from lxml import etree

from pers.config import Config
from pers.xml_records import (
    AuthorXMLRecord,
    AuthorPublicationsXMLRecord,
    PublicationXMLRecord,
)

CONFIG = Config()
AUTH = (CONFIG.ELEMENTS_USER, CONFIG.ELEMENTS_PASSWORD)
PROXIES = {"http": CONFIG.QUOTAGUARD_STATIC_URL, "https": CONFIG.QUOTAGUARD_STATIC_URL}
logger = logging.getLogger(__name__)


@define
class ElementsClient:
    api_base: str = field(default="https://pubdata-dev.mit.edu:8091/secure-api/v5.5")

    def make_request(self, path: str, **kwargs) -> str | None:
        """Make an API request to Symplectic Elements API."""
        try:
            response = requests.get(
                url=f"{self.api_base}/{path.removeprefix('/')}",
                proxies=PROXIES,
                auth=AUTH,
                timeout=10,
                **kwargs,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.exception(error)
        else:
            return response.text

    def get_author_info(self, author_id: str | int):
        return self.make_request(f"users/{author_id}")

    def get_author_publications_info(self, author_id: str | int):
        return self._get_paged(f"users/{author_id}/publications?&detail=full")

    def get_publication_info(self, publication_id: str | int):
        return self.make_request(f"publications/{publication_id}")

    def _get_paged(self, path):
        page = self.make_request(path)
        yield page
        page_element = etree.fromstring(page.encode(encoding="utf-8"))
        next_page = page_element.xpath("//*[local-name()='page'][@position='next']/@href")
        if next_page:
            next_page_path = next_page[0].split(self.api_base)[1]
            yield from self._get_paged(next_page_path)


if __name__ == "__main__":
    elements_client = ElementsClient()

    # author info
    author_info_xml = elements_client.get_author_info(author_id=12338)
    author_xml_record = AuthorXMLRecord(data=author_info_xml).parse()
    print(author_xml_record)

    # list of qualifying author publications
    author_publications_xml = elements_client.get_author_publications_info(
        author_id=12338
    )
    publications_list = []
    for page in author_publications_xml:
        if publications := AuthorPublicationsXMLRecord(data=page).parse(
            author_xml_record
        ):
            publications_list.extend(publications)
    print(len(set([d["publication_id"] for d in publications_list])))

    # publication info
    publication_xml = elements_client.get_publication_info(publication_id="206966")
    publication_xml_record = PublicationXMLRecord(data=publication_xml).parse()
    print(publication_xml_record)
