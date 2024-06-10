from unittest.mock import MagicMock, patch

import pytest
from requests import RequestException  # type: ignore

from src.config import SMART_DRAFT_BASE_URL
from src.smart_draft_api import (generate_api_endpoint, send_intent_response,
                                 send_validation_response)


class TestSendIntentResponse:
    @pytest.fixture
    def mock_requests_put(self):
        with patch('requests.put') as mock:
            yield mock

    @pytest.fixture
    def mock_requests_post(self):
        with patch('requests.post') as mock:
            yield mock

    @pytest.fixture
    def mock_generate_endpoint_url(self):
        with patch('src.smart_draft_api.generate_api_endpoint',
                   return_value='http://url.com/endpoint') as mock:
            yield mock

    @pytest.mark.parametrize(
            "status_code, exception, expected_exception, exception_message",
            [
                (200, None, None, None),
                (400, None, None, None),
                (None, RequestException, RuntimeError,
                 "Failed to send intent response: Network failure")
            ]
    )
    def test_send_intent_response(
            self, mock_requests_put, mock_generate_endpoint_url, status_code,
            exception, expected_exception, exception_message):
        if exception:
            mock_requests_put.side_effect = exception(exception_message)
        else:
            mock_response = MagicMock(status_code=status_code)
            mock_requests_put.return_value = mock_response

        conversation_id = 123
        identified_intent = "interpreter_booking"

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                send_intent_response(conversation_id, identified_intent)
            assert exception_message in str(exc_info.value)
        else:
            send_intent_response(conversation_id, identified_intent)
            assert mock_response.status_code == status_code

    @pytest.mark.parametrize(
            "status_code, exception, expected_exception, exception_message",
            [
                (200, None, None, None),
                (400, None, None, None),
                (None, RequestException, RuntimeError,
                 "Failed to send validation response: Network failure")
            ]
    )
    def test_send_validation_response(
            self, mock_requests_post, mock_generate_endpoint_url, status_code,
            exception, expected_exception, exception_message):
        if exception:
            mock_requests_post.side_effect = exception(exception_message)
        else:
            mock_response = MagicMock(status_code=status_code)
            mock_requests_post.return_value = mock_response

        intent = "interpreter_booking"
        identified_params = {"language": "en", "duration": 30}
        conversation_id = 123

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                send_validation_response(
                        intent, identified_params, conversation_id)
            assert exception_message in str(exc_info.value)
        else:
            send_validation_response(
                    intent, identified_params, conversation_id)
            assert mock_response.status_code == status_code


class TestGenerateAPIEndpoint:
    @pytest.mark.parametrize("endpoint, intent, conversation_id, expected", [
        ("intent-detection", None, 123,
         f"{SMART_DRAFT_BASE_URL}/conversations/123/intent-detected"),
        ("validation", "book-interpreter", None,
         f"{SMART_DRAFT_BASE_URL}/intents/book-interpreter/validate"),
        ("execution", "book-interpreter", None,
         f"{SMART_DRAFT_BASE_URL}/intents/book-interpreter/execute"),
        ("incorrect", None, None, ValueError),
    ])
    def test_generate_api_endpoint(self, endpoint, intent, conversation_id,
                                   expected):
        if isinstance(expected, str):
            assert generate_api_endpoint(
                    endpoint, intent, conversation_id) == expected
        else:
            with pytest.raises(expected):
                generate_api_endpoint(endpoint, intent, conversation_id)
