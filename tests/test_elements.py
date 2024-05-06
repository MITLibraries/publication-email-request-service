def test_elements_get_author_info_success(
    elements_client,
    mocked_elements_api_get_author_info,
    mocked_elements_api_response_author_info,
):
    assert (
        elements_client.get_author_info(author_id=123)
        == mocked_elements_api_response_author_info
    )


def test_elements_get_author_info_author_does_not_exist_return_none_log_error(
    elements_client, mocked_elements_api_get_author_info, caplog
):
    response = elements_client.get_author_info(author_id=0)
    assert response is None
    assert "404 Client Error" in caplog.text


def test_elements_get_author_publications_info_success(
    elements_client,
    mocked_elements_api_get_author_publications_info,
    mocked_elements_api_response_author_publications_info,
):
    assert (
        next(elements_client.get_author_publications_info(author_id=123))
        == mocked_elements_api_response_author_publications_info
    )


def test_elements_get_author_publications_info_author_does_not_exist_return_none_log_error(
    elements_client, mocked_elements_api_get_author_publications_info, caplog
):
    response = elements_client.get_author_publications_info(author_id=0)
    assert next(response) is None
    assert "404 Client Error" in caplog.text


def test_elements_get_publication_info_success(
    elements_client,
    mocked_elements_api_get_publication_info,
    mocked_elements_api_response_publication_info,
):
    assert (
        elements_client.get_publication_info(publication_id="000001")
        == mocked_elements_api_response_publication_info
    )


def test_elements_get_publication_info_publication_does_not_exist_return_none_log_error(
    elements_client, mocked_elements_api_get_publication_info, caplog
):
    response = elements_client.get_publication_info(publication_id=0)
    assert response is None
    assert "404 Client Error" in caplog.text
