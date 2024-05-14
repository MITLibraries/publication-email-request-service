import pytest

import requests_mock

from click.testing import CliRunner
from lxml import etree

from pers.elements import ElementsClient


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "None")
    monkeypatch.setenv("WORKSPACE", "test")
    monkeypatch.setenv("ELEMENTS_USER", "user")
    monkeypatch.setenv("ELEMENTS_PASSWORD", "password")


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def elements_client():
    return ElementsClient()


@pytest.fixture(scope="session", autouse=True)
def global_requests_mock():
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def mocked_elements_api_response_author_info():
    with open("tests/fixtures/elements_api_responses/author_info.xml") as f:
        tree = etree.parse(f)
        api_response = etree.tostring(tree, encoding="unicode")
        return api_response


@pytest.fixture
def mocked_elements_api_response_author_publications_info():
    with open("tests/fixtures/elements_api_responses/author_publications_info.xml") as f:
        tree = etree.parse(f)
        api_response = etree.tostring(tree, encoding="unicode")
        return api_response


@pytest.fixture
def mocked_elements_api_response_publication_info():
    with open("tests/fixtures/elements_api_responses/publication_info.xml") as f:
        tree = etree.parse(f)
        api_response = etree.tostring(tree, encoding="unicode")
        return api_response


@pytest.fixture
def mocked_elements_api_get_author_info(
    elements_client, global_requests_mock, mocked_elements_api_response_author_info
):
    url = "{api_base}/users/{author_id}"

    global_requests_mock.get(
        url.format(api_base=elements_client.api_base, author_id=123),
        text=mocked_elements_api_response_author_info,
    )
    global_requests_mock.get(
        url.format(api_base=elements_client.api_base, author_id=0),
        status_code=404,
    )


@pytest.fixture
def mocked_elements_api_get_author_publications_info(
    elements_client,
    global_requests_mock,
    mocked_elements_api_response_author_publications_info,
):
    url = "{api_base}/users/{author_id}/publications?&detail=full"
    global_requests_mock.get(
        url.format(api_base=elements_client.api_base, author_id=123),
        text=mocked_elements_api_response_author_publications_info,
    )
    global_requests_mock.get(
        url.format(api_base=elements_client.api_base, author_id=0),
        status_code=404,
    )


@pytest.fixture
def mocked_elements_api_get_publication_info(
    elements_client, global_requests_mock, mocked_elements_api_response_publication_info
):
    url = "{api_base}/publications/{publication_id}"
    global_requests_mock.get(
        url.format(api_base=elements_client.api_base, publication_id="000001"),
        text=mocked_elements_api_response_publication_info,
    )
    global_requests_mock.get(
        url.format(api_base=elements_client.api_base, publication_id=0), status_code=404
    )
