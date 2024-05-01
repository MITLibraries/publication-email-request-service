import datetime as dt
import xml.etree.ElementTree as ET

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "api": "http://www.symplectic.co.uk/publications/api",
}


def extract_attribute(root: ET.Element, search_string: str, attribute: str) -> str:
    value = ""
    try:
        if (element := root.find(search_string, NS)) is not None:
            return element.get(attribute, "")
    except AttributeError:
        return value
    return value


def extract_field(root: ET.Element, search_string: str) -> str | None:
    field = ""
    try:
        if (element := root.find(search_string, NS)) is not None:
            return element.text
    except AttributeError:
        return field
    return field


def get_pub_date(root: ET.Element) -> dt.date | None:
    try:
        year = int(
            extract_field(root, ".//api:field[@name='publication-date']//api:year")  # type: ignore[arg-type]
        )
    except ValueError:
        return None
    try:
        month = int(
            extract_field(root, ".//api:field[@name='publication-date']//api:month")  # type: ignore[arg-type]
        )
    except ValueError:
        month = 1
    try:
        day = int(extract_field(root, ".//api:field[@name='publication-date']//api:day"))  # type: ignore[arg-type]
    except ValueError:
        day = 1
    try:
        pub_date = dt.date(year, month, day)
    except ValueError:
        pub_date = dt.date(year, 1, 1)
    return pub_date


def parse_publication_xml(pubs_xml: str):
    root = ET.fromstring(pubs_xml)
    PAPER_DATA = {
        "_citation": extract_field(root, ".//api:field[@name='c-citation']/api:text"),
        "doi": extract_field(root, ".//api:field[@name='doi']/api:text"),
        "publisher": extract_field(root, ".//api:field[@name='publisher']/api:text"),
        "c_method_of_acquisition": "",
        "id": root.find(".//api:object", NS).get("id"),
        "c_publisher_related_email_message": "",
        "publication_year": extract_field(
            root, ".//api:field[@name='publication-date']/api:date/api:year"
        ),
        "title": extract_field(root, "atom:title"),
        "journal_name": extract_field(root, ".//api:field[@name='journal']/api:text"),
        "journal_elements_url": extract_attribute(root, ".//api:journal", "href"),
        "volume": extract_field(root, ".//api:field[@name='volume']/api:text"),
        "issue": extract_field(root, ".//api:field[@name='issue']/api:text"),
    }
    return PAPER_DATA


def parse_journal_policies(journal_policies_xml: str) -> dict:
    root = ET.fromstring(journal_policies_xml)
    POLICY_DATA = {
        "c_method_of_acquisition": extract_field(
            root, ".//api:field[@name='c-method-of-acquisition']/api:text"
        ),
        "c_publisher_related_email_message": extract_field(
            root,
            ".//api:field"
            "[@name='c-"
            "publisher-related-"
            "email-message']/"
            "api:text",
        ),
    }
    return POLICY_DATA


def parse_author_pubs_xml(author_pubs_xml: str, author_data: dict) -> list:
    """Takes a an author-publications record feed from Symplectic
    Elements, parses each record according to local rules for which
    publications should be requested based on certain metadata fields, and
    returns a list of publication IDs that should be imported into Solenoid and
    requested from the author.
    """
    RESULTS = []

    root = ET.fromstring(author_pubs_xml)
    pub_id = None
    title = None
    for entry in root.findall("./atom:entry", NS):
        if (
            pub_element := entry.find(".//api:object[@category='publication']", NS)
        ) is not None:
            pub_id = pub_element.get("id")
        if (
            title_element := entry.find(".//api:field[@name='title']/api:text", NS)
        ) is not None:
            title = title_element.text
        # Filter for papers to be requested based on various criteria
        pub_date = get_pub_date(entry)
        if not pub_date:
            pass
        # Paper was published after OA policy enacted
        elif pub_date <= dt.date(2009, 3, 18):
            continue
        # Paper was published while author was MIT faculty
        elif pub_date < dt.date.fromisoformat(
            author_data["start_date"]
        ) or pub_date > dt.date.fromisoformat(author_data["end_date"]):
            continue
        # Paper does not have a library status
        if entry.find(".//api:library-status", NS):
            continue
        # Publication type is either a journal article, book chapter, or
        # conference proceeding
        pub_type = extract_attribute(entry, ".//api:object", "type-id")
        if pub_type not in ("3", "4", "5"):
            continue
        # Paper does not have any OA policy exceptions, except for "Waiver"
        # which we do request
        if entry.find(".//api:oa-policy-exception", NS):
            exceptions = [
                e.text for e in entry.findall(".//api:oa-policy-exception/api:type", NS)
            ]
            if "Waiver" not in exceptions:
                continue
        # If paper has a manual entry record in Elements, none of the
        # following fields are true
        if entry.find(".//api:record[@source-name='manual']", NS):
            if (
                entry.find(".//api:field[@name='c-do-not-request']/api:boolean", NS).text
                == "true"
                or entry.find(".//api:field[@name='c-optout']/api:boolean", NS).text
                == "true"
                or entry.find(".//api:field[@name='c-received']/api:boolean", NS).text
                == "true"
                or entry.find(".//api:field[@name='c-requested']/api:boolean", NS).text
                == "true"
            ):
                continue
        # If paper has a dspace record in Elements, status is not 'Public'
        # or 'Private' (in either case it has been deposited and should not
        # be requested)
        if entry.find(".//api:record[@source-name='dspace']", NS):
            status = extract_field(
                entry, ".//api:field[@name='repository-status']/api:text"
            )
            if status == "Public" or status == "Private":
                continue
        # If paper has passed all the checks above, add it to request list
        RESULTS.append({"id": pub_id, "title": title})
    return RESULTS


def parse_author_xml(author_xml: str) -> dict:
    root = ET.fromstring(author_xml)
    AUTHOR_DATA = {
        "email_address": extract_field(root, ".//api:email-address"),
        "first_name": extract_field(root, ".//api:first-name"),
        "last_name": extract_field(root, ".//api:last-name"),
        "mit_id": root.find(".//api:object", NS).get("proprietary-id"),
        "dlc": extract_field(root, ".//api:primary-group-descriptor"),
        "start_date": extract_field(root, ".//api:arrive-date"),
    }
    try:
        AUTHOR_DATA["end_date"] = root.find(".//api:leave-date", NS).text
    except AttributeError:
        AUTHOR_DATA["end_date"] = "3000-01-01"
    return AUTHOR_DATA
