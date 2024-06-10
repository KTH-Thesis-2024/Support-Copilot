import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError  # type: ignore

from src.lambda_handler import handle_intent_request, \
    handle_extraction_request, lambda_handler, retrieve_data
from tests.test_utilites import generate_validation_error


@pytest.fixture
def mock_send_intent_response():
    with patch('src.lambda_handler.send_intent_response') as mock:
        yield mock


@pytest.fixture
def mock_send_validation_response():
    with patch('src.lambda_handler.send_validation_response') as mock:
        yield mock


class TestLambdaHandler:
    context = Mock()

    @pytest.fixture
    def intent_event(self):
        return {
            "Records": [{
                "body": json.dumps({"conversation_id": 1}),
                "eventSourceARN": "blabla.s1233-intent.hello"
            }]
        }

    @pytest.fixture
    def extract_event(self):
        return {
            "Records": [{
                "body": json.dumps({"conversation_id": 1, "intent": "test"}),
                "eventSourceARN": "blabla.s1233-extraction.hello"
            }]
        }

    @pytest.fixture
    def mock_retrieve_data(self):
        with patch('src.lambda_handler.retrieve_data',
                   return_value=({"message": "test"})) as mock_retrieve_data:
            yield mock_retrieve_data

    @pytest.fixture
    def mock_handle_intent_request(self):
        with patch(
                'src.lambda_handler.handle_intent_request') as mock:
            yield mock

    @pytest.fixture
    def mock_handle_extraction_request(self):
        with patch('src.lambda_handler.handle_extraction_request') as mock:
            yield mock

    @pytest.fixture
    def mock_logger(self):
        with patch('src.lambda_handler.logger') as mock:
            yield mock

    @pytest.mark.parametrize(
            "event, mock_handle_request, request_args", [
                ("intent_event", "mock_handle_intent_request",
                 (1, {"message": "test"})),
                ("extract_event", "mock_handle_extraction_request",
                 ({"message": "test"},
                  {"conversation_id": 1, "intent": "test"}, 1))
            ])
    def test_lambda_handler_success(
            self, request, mock_retrieve_data, event,
            mock_handle_request, request_args):
        event = request.getfixturevalue(event)
        mock_handle_request = request.getfixturevalue(mock_handle_request)

        lambda_handler(event, self.context)

        mock_retrieve_data.assert_called_once()
        mock_handle_request.assert_called_once_with(*request_args)

    def test_lambda_handler_unknown_event_source(
            self, mock_retrieve_data, intent_event, mock_logger):
        intent_event["Records"][0][
            "eventSourceARN"] = "blabla.s1233-unknown.hello"

        lambda_handler(intent_event, self.context)

        mock_logger.error.assert_called_with("Failed to handle request : 1")

    def test_lambda_handler_intent_identification_validation_error(
            self, mock_handle_intent_request, mock_retrieve_data,
            mock_send_intent_response, intent_event):
        mock_handle_intent_request.side_effect = (
            generate_validation_error(
                    title="IntentRequest",
                    error_type="json_type",
                    input_data={"conversation_id": 1}))

        conversation_id = 1
        s3_payload = {"message": "test"}

        lambda_handler(intent_event, self.context)

        mock_handle_intent_request.assert_called_once_with(
                conversation_id, s3_payload)
        mock_retrieve_data.assert_called_once()
        mock_handle_intent_request.assert_called_once_with(
                conversation_id, s3_payload)
        assert "IntentRequest" in str(mock_send_intent_response.call_args_list)
        assert "json_type" in str(mock_send_intent_response.call_args_list)

    def test_lambda_handler_extraction_validation_error(
            self, mock_handle_extraction_request, mock_retrieve_data,
            extract_event, mock_send_validation_response):
        mock_handle_extraction_request.side_effect = generate_validation_error(
                title="ExtractRequest",
                error_type="json_type",
                input_data={"conversation_id": 1})

        sqs_body = {"conversation_id": 1, "intent": "test"}
        s3_payload = {"message": "test"}
        conversation_id = 1

        lambda_handler(extract_event, self.context)

        mock_handle_extraction_request.assert_called_once_with(
                s3_payload, sqs_body, conversation_id)
        mock_retrieve_data.assert_called_once()
        assert "ExtractRequest" in str(
                mock_send_validation_response.call_args_list)
        assert "json_type" in str(mock_send_validation_response.call_args_list)

    def test_lambda_handler_intent_exception_in_retrieve_data(
            self, mock_retrieve_data, intent_event, mock_send_intent_response):
        mock_retrieve_data.side_effect = Exception("Test Exception")

        sqs_body = {"conversation_id": 1}
        conversation_id = 1

        lambda_handler(intent_event, self.context)

        mock_retrieve_data.assert_called_once_with(sqs_body)
        mock_send_intent_response.assert_called_once_with(
                conversation_id, "Test Exception")

    def test_lambda_handler_extract_exception_in_retrieve_data(
            self, mock_retrieve_data, mock_send_validation_response,
            extract_event):
        exception_message = "Test Exception"
        mock_retrieve_data.side_effect = Exception(exception_message)

        sqs_body = {"conversation_id": 1, "intent": "test"}
        intent = "test"
        conversation_id = 1

        lambda_handler(extract_event, self.context)

        mock_retrieve_data.assert_called_once_with(sqs_body)
        mock_send_validation_response.assert_called_once_with(
                intent, {"error": exception_message}, conversation_id)


class TestRetrieveData:
    @pytest.fixture
    def mock_sqs_message(self):
        with patch('src.lambda_handler.SQSMessage') as mock:
            yield mock

    @pytest.fixture
    def mock_retrieve_s3_payload(self):
        with patch('src.lambda_handler.retrieve_s3_payload') as mock:
            yield mock

    def test_retrieve_data_success(
            self, mock_retrieve_s3_payload, mock_sqs_message):
        mock_retrieve_s3_payload.return_value = {"data": "value"}
        mock_sqs_message.return_value = MagicMock(
                payload_path="path/to/s3/object")

        sqs_payload = {"payload_path": "path/to/s3/object"}
        s3_payload = {"data": "value"}

        result_payload = retrieve_data(sqs_payload)

        mock_sqs_message.assert_called_once_with(**sqs_payload)
        mock_retrieve_s3_payload.assert_called_once_with(
                sqs_payload['payload_path'])
        assert result_payload == s3_payload

    def test_retrieve_data_validation_error(
            self, mock_retrieve_s3_payload, mock_sqs_message):
        mock_sqs_message.return_value = MagicMock(payload_path="invalid/path")

        error_title = "S3Payload"
        error_type = "json_type"
        error_input = {"payload_path": "invalid/path"}

        mock_retrieve_s3_payload.side_effect = generate_validation_error(
                title=error_title,
                error_type=error_type,
                input_data=error_input,
        )

        sqs_payload = {"payload_path": "invalid/path"}

        with pytest.raises(ValidationError) as exc_info:
            retrieve_data(sqs_payload)

        mock_sqs_message.assert_called_once_with(**sqs_payload)
        mock_retrieve_s3_payload.assert_called_once_with(
                sqs_payload['payload_path'])
        assert error_title in str(exc_info.value)
        assert error_type in str(exc_info.value)
        assert str(error_input) in str(exc_info.value)


class TestHandleIntentDetectionRequest:
    @patch('src.lambda_handler.IntentRequest',
           return_value=MagicMock(conversation_id=123))
    @patch('src.lambda_handler.identify_intent', return_value="1")
    def test_handle_intent_detection_request_success(
            self, mock_identify_intent, mock_intent_request,
            mock_send_intent_response):
        identified_intent = "1"
        conversation_id = 123
        s3_payload = {"data": "value"}

        handle_intent_request(conversation_id, s3_payload)

        mock_intent_request.assert_called_once_with(**s3_payload)
        mock_identify_intent.assert_called_once_with(
                mock_intent_request.return_value)
        mock_send_intent_response.assert_called_once_with(
                conversation_id, identified_intent)


class TestHandleExtractionRequest:
    @patch('src.lambda_handler.ExtractRequest',
           return_value=MagicMock(intent="test"))
    @patch('src.lambda_handler.extract_data',
           return_value={"data": "value"})
    def test_handle_extraction_request_success(
            self, mock_extract_data, mock_extract_request,
            mock_send_validation_response):
        s3_payload = {"data": "value"}
        sqs_payload = {"intent": "test"}
        conversation_id = 123

        handle_extraction_request(s3_payload, sqs_payload, conversation_id)

        mock_extract_request.assert_called_once_with(**s3_payload)
        mock_extract_data.assert_called_once_with(
                mock_extract_request.return_value)
        mock_send_validation_response.assert_called_once_with(
                sqs_payload["intent"], s3_payload, conversation_id)
