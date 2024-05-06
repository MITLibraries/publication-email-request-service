import logging
from datetime import date, datetime
from typing import Generator

from attrs import define, field
from lxml import etree

logger = logging.getLogger(__name__)
OA_POLICY_ENACTED_DATE = date(2009, 3, 18)


@define
class XMLRecord:
    data: str | Generator = field(repr=False)
    nsmap: dict = field(factory=dict)
    _root: etree._Element = field(default=None, repr=False)

    def __attrs_post_init__(self) -> None:
        """Get XML namespaces."""
        self.nsmap = {
            prefix: default_uri
            for prefix, default_uri in self.root.nsmap.items()
            if prefix
        }

    @property
    def root(self) -> etree._Element:
        """Property to parse raw xml bytes and return lxml Element.

        This property uses a cached instance at self._root if present to avoid re-parsing
        the XML.
        """
        # lxml note: "Use specific 'len(elem)' or 'elem is not None' test instead."
        if self._root is None:
            self._root = etree.fromstring(self.data.encode("utf-8"))
        return self._root

    def xpath_query(
        self, xpath_expr: str, element: etree._Element | None = None
    ):  # noqa: ANN401
        """Perform XPath query.

        This method automatically includes the namespaces defined for the class.
        """
        if element is None:
            return self.root.xpath(xpath_expr, namespaces=self.nsmap)
        return element.xpath(xpath_expr, namespaces=self.nsmap)

    @staticmethod
    def get_string_from_xpath(
        values: list,
        delimiter: str = " ",
    ):
        if values:
            unique_values = list(set(values))
            return delimiter.join([element for element in unique_values]) or None

    @staticmethod
    def get_string_list_from_xpath(values: list[str]):
        if values:
            unique_values = list(set(values))
            return unique_values or []
        return []


@define
class AuthorXMLRecord(XMLRecord):
    """Class for parsing XML with author details.

    Parses the XML returned from GET request to API endpoint:
    https://pubdata-dev.mit.edu:8091/secure-api/v5.5/users/<author_id>/
    """

    def parse(self):
        author_info = {
            "email": self.get_string_from_xpath(
                self.xpath_query(".//api:email-address/text()")
            ),
            "first_name": self.get_string_from_xpath(
                self.xpath_query(".//api:first-name/text()")
            ),
            "last_name": self.get_string_from_xpath(
                self.xpath_query(".//api:last-name/text()")
            ),
            "mit_id": self.get_string_from_xpath(
                self.xpath_query(".//api:object/@proprietary-id")
            ),
            "dlc": self.get_string_from_xpath(
                self.xpath_query(".//api:primary-group-descriptor/text()")
            ),
            "start_date": self.get_string_from_xpath(
                self.xpath_query(".//api:start-date/text()")
            ),
            "end_date": self.get_string_from_xpath(
                self.xpath_query(".//api:leave-date/text()")
            )
            or "3000-01-01",
        }
        return author_info


@define
class AuthorPublicationsXMLRecord(XMLRecord):
    """Class for parsing XML with list of author publications.

    Parses the XML returned from GET request to API endpoint:
    https://pubdata-dev.mit.edu:8091/secure-api/v5.5/users/<author_id>/publications?detail=full
    """

    def parse(self, author_xml_record: dict):
        """Get list of publications that qualify for an email request."""
        filtered_publications = []
        publications = self.xpath_query(".//api:object")
        for publication in publications:
            publication_info = {
                # get values from attributes of a single tag
                "id": self.get_string_from_xpath(self.xpath_query("@id", publication)),
                "publication_type": self.get_string_from_xpath(
                    self.xpath_query("@type-id", publication)
                ),
                # get values from attributes of multiple tags
                "source_names": self.get_string_list_from_xpath(
                    self.xpath_query(".//api:record/@source-name", publication)
                ),
                # get values by searching through tag
                "title": self.get_string_from_xpath(
                    [
                        self.xpath_query(
                            ".//api:field[@name='title']/api:text/text()", publication
                        )[0]
                    ]
                ),
                "dspace_repository_status": self.get_string_from_xpath(
                    self.xpath_query(
                        ".//api:record[@source-name='dspace']//api:field[@name='repository-status']/api:text/text()",
                        publication,
                    )
                ),
                "library_status": self.get_string_from_xpath(
                    self.xpath_query(".//api:library-status/text()", publication)
                ),
                # get values by searching through nested tags
                "exceptions": self.get_string_list_from_xpath(
                    self.xpath_query(
                        ".//api:oa-policy-exception/api:type/text()", publication
                    )
                ),
                "c_do_not_request": self.get_string_from_xpath(
                    self.xpath_query(
                        ".//api:field[@name='c-do-not-request']/api:boolean/text()",
                        publication,
                    )
                ),
                "c_optout": self.get_string_from_xpath(
                    self.xpath_query(
                        ".//api:field[@name='c-optout']/api:boolean/text()", publication
                    )
                ),
                "c_received": self.get_string_from_xpath(
                    self.xpath_query(
                        ".//api:field[@name='c-received']/api:boolean/text()", publication
                    )
                ),
                "c_requested": self.get_string_from_xpath(
                    self.xpath_query(
                        ".//api:field[@name='c-requested']/api:boolean/text()",
                        publication,
                    )
                ),
                # get values by custom methods (require additional steps)
                "publication_date": self.get_publication_date(
                    year=self.xpath_query(
                        ".//api:field[@name='publication-date']//api:year/text()",
                        publication,
                    )[0]
                    or None,
                    month=self.xpath_query(
                        ".//api:field[@name='publication-date']//api:month/text()",
                        publication,
                    )[0]
                    or None,
                    day=self.xpath_query(
                        ".//api:field[@name='publication-date']//api:day/text()",
                        publication,
                    )[0]
                    or None,
                ),
            }

            # if self.check_publication(publication_info, author_xml_record):
            filtered_publications.append(
                {
                    "publication_id": publication_info["id"],
                    "publication_title": publication_info["title"],
                }
            )
        return filtered_publications

    @classmethod
    def check_publication(cls, publication_info: dict, author_info: dict):
        """Check if publication meets criteria for an email request."""

        # the publication was published after OA policy enacted
        if publication_info["publication_date"] <= OA_POLICY_ENACTED_DATE:
            return False

        # the publication was published while author was MIT-affiliated
        # publication date must not be before author's start date
        # publication date must not be after author's end date
        if (
            publication_info["publication_date"]
            < datetime.strptime(author_info["start_date"], "%Y-%m-%d").date()
        ) or (
            publication_info["publication_date"]
            > datetime.strptime(author_info["end_date"], "%Y-%m-%d").date()
        ):
            return False

        # the publication must not be assigned a library status
        if publication_info["library_status"]:
            return False

        # the publication type is either a journal article, book chapter, or
        # conference proceeding
        if publication_info["publication_type"] not in ("3", "4", "5"):
            return False

        # if the publication has any exceptions that exempt it from Open Access policy
        # "Waiver" must be listed as one of these exceptions
        if exceptions := publication_info["exceptions"]:
            if "Waiver" not in exceptions:
                return False

        # if the publication info is manually entered on Symplectic Elements
        # the fields [c_do_not_request, c_optout, c_received, c_requested] must indicate "false"
        if "manual" in publication_info["source_names"]:
            if (
                (
                    publication_info["c_do_not_request"]
                    and publication_info["c_do_not_request"] == "true"
                )
                or (
                    publication_info["c_optout"]
                    and publication_info["c_optout"] == "true"
                )
                or (
                    publication_info["c_received"]
                    and publication_info["c_received"] == "true"
                )
                or (
                    publication_info["c_requested"]
                    and publication_info["c_requested"] == "true"
                )
            ):
                return False

        # If paper has a dspace record in Elements, status is not 'Public'
        # or 'Private' (in either case it has been deposited and should not
        # be requested)
        if "dspace" in publication_info["source_names"]:
            dspace_repository_status = publication_info["dspace_repository_status"]
            if dspace_repository_status in ["Public", "Private"]:
                return False
        return True

    @classmethod
    def get_publication_date(
        cls, year: str | None = None, month: str | None = None, day: str | None = None
    ):
        """Create date using parsed date components from tag.

        The publication date must have a known "year" value.
        If the publication date does not have valid "month" and/or "day" values,
        the method will default to January 1st on the year of publication.
        """
        try:
            year = int(year)
        except TypeError:
            return None

        try:
            month = int(month)
        except TypeError:
            month = 1

        try:
            day = int(day)
        except TypeError:
            day = 1

        return date(year, month, day)


class PublicationXMLRecord(XMLRecord):
    def parse(self):
        return {
            "_citation": self.get_string_from_xpath(
                self.xpath_query(".//api:field[@name='c-citation']/api:text/text()")
            ),
            "doi": self.get_string_from_xpath(
                self.xpath_query(".//api:field[@name='doi']/api:text/text()")
            ),
            "publisher": self.get_string_from_xpath(
                self.xpath_query(".//api:field[@name='publisher']/api:text/text()")
            ),
            # "c_method_of_acquisition": "",
            "id": self.get_string_from_xpath(self.xpath_query(".//api:object/@id")),
            # "c_publisher_related_email_message": "",
            # "publication_year": "",
            # "title": "",
            "journal_name": self.get_string_from_xpath(
                self.xpath_query(".//api:field[@name='journal']/api:text/text()")
            ),
            "journal_elements_url": self.get_string_from_xpath(
                self.xpath_query(".//api:field[@name='journal']/@href")
            ),
            "volume": self.get_string_from_xpath(
                self.xpath_query(".//api:field[@name='volume']/api:text/text()")
            ),
            "issue": self.get_string_from_xpath(
                self.xpath_query(".//api:field[@name='issue']/api:text/text()")
            ),
        }
