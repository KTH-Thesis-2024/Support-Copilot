from unittest.mock import MagicMock, patch

import pytest

from src.config import LLAMA_INTENT_PROMPT_TEMPLATE as PROMPT_TEMPLATE
from src.intent_identification_service import generate_prompt, \
    identify_intent, validate_llm_response
from src.models import Intent
from tests.test_utilites import generate_validation_error


class TestProcessIntent:
    mock_prompt = "Generated prompt"
    mock_llm_response = "LLM response"

    @pytest.fixture
    def mock_generate_prompt(self):
        with patch('src.intent_identification_service.generate_prompt',
                   return_value=self.mock_prompt) as mock:
            yield mock

    @pytest.fixture
    def mock_prompt_llm(self):
        with patch('src.intent_identification_service.prompt_llm',
                   return_value=self.mock_llm_response) as mock:
            yield mock

    @pytest.fixture
    def mock_validate_llm_response(self):
        with (patch('src.intent_identification_service.validate_llm_response')
              as mock):
            yield mock

    def test_process_intent_valid_intent(
            self, mock_generate_prompt, mock_validate_llm_response,
            mock_prompt_llm):
        validated_llm_response = "valid_intent"
        operation_type = {'operation_type': 'intent'}
        intent_request = MagicMock()

        mock_validate_llm_response.return_value = validated_llm_response

        result = identify_intent(intent_request)

        mock_generate_prompt.assert_called_once_with(intent_request)
        mock_prompt_llm.assert_called_once_with(
                self.mock_prompt, **operation_type)
        mock_validate_llm_response.assert_called_once_with(
                self.mock_llm_response, intent_request.intents)
        assert result == "valid_intent"

    def test_process_intent_invalid_intent_retry_success(
            self, mock_generate_prompt, mock_prompt_llm,
            mock_validate_llm_response):
        first_llm_response = self.mock_llm_response
        second_llm_response = "LLM response retry"
        first_validated_llm_response = "invalid_intent"
        second_validated_llm_response = "valid_intent_retry"
        operation_type = {'operation_type': 'intent'}
        intent_request = MagicMock()

        mock_prompt_llm.side_effect = [first_llm_response, second_llm_response]
        mock_validate_llm_response.side_effect = [
            first_validated_llm_response, second_validated_llm_response]

        result = identify_intent(intent_request)

        assert mock_prompt_llm.call_count == 2
        mock_prompt_llm.assert_any_call(self.mock_prompt, **operation_type)
        mock_prompt_llm.assert_any_call(
                self.mock_prompt, **operation_type, change_llm=True)
        assert mock_validate_llm_response.call_count == 2
        mock_validate_llm_response.assert_any_call(
                first_llm_response, intent_request.intents)
        mock_validate_llm_response.assert_any_call(
                second_llm_response, intent_request.intents)
        assert result == "valid_intent_retry"

    def test_process_intent_invalid_intent_final_failure(
            self, mock_generate_prompt, mock_prompt_llm,
            mock_validate_llm_response):
        validated_llm_response = "invalid_intent"
        operation_type = {'operation_type': 'intent'}
        intent_request = MagicMock()

        mock_prompt_llm.side_effect = [
            self.mock_llm_response, self.mock_llm_response]
        mock_validate_llm_response.return_value = validated_llm_response

        result = identify_intent(intent_request)

        assert mock_prompt_llm.call_count == 2
        mock_prompt_llm.assert_any_call(self.mock_prompt, **operation_type)
        mock_prompt_llm.assert_any_call(
                self.mock_prompt, **operation_type, change_llm=True)
        assert mock_validate_llm_response.call_count == 2
        mock_validate_llm_response.assert_called_with(
                self.mock_llm_response, intent_request.intents)
        assert result == "invalid_intent"


class TestGeneratePrompt:
    mock_intents = "intents_data"
    mock_messages = "messages_data"

    @pytest.fixture
    def mock_prompt_template(self):
        with patch('src.intent_identification_service.PromptTemplate') as mock:
            yield mock

    @pytest.fixture
    def mock_intent_request(self):
        with patch('src.intent_identification_service.IntentRequest') as mock:
            yield mock

    def test_generate_prompt(self, mock_prompt_template, mock_intent_request):
        mock_intent_request.return_value.output_stringified_intents \
            .return_value = self.mock_intents
        mock_intent_request.return_value.output_stringified_messages \
            .return_value = self.mock_messages

        mock_prompt_template.return_value.format.return_value = ("Formatted "
                                                                 "prompt")

        result = generate_prompt(mock_intent_request.return_value)

        mock_prompt_template.assert_called_once_with(
                template=PROMPT_TEMPLATE,
                input_variables=["intent_list", "email_conversation"])
        mock_prompt_template.return_value.format.assert_called_once_with(
                intent_list=self.mock_intents,
                email_conversation=self.mock_messages)

        assert result == "Formatted prompt"

    def test_generate_prompt_with_error(
            self, mock_prompt_template, mock_intent_request):
        mock_intent_output = mock_intent_request.return_value
        mock_intent_output.output_stringified_intents.return_value = (
            self.mock_intents)
        mock_intent_output.output_stringified_messages.return_value = (
            self.mock_messages)

        mock_prompt_template.return_value.format.side_effect = Exception(
                "Formatting error")

        with pytest.raises(Exception) as exc_info:
            generate_prompt(mock_intent_request.return_value)

        assert str(exc_info.value) == "Formatting error"


class TestValidateLLMResponse:
    intents = [Intent(id=1,
                      slug="request_translation",
                      description="Request translation"),
               Intent(id=2,
                      slug="interpreter_booking",
                      description="Interpreter booking")
               ]

    def test_validate_llm_response_valid(self):
        response = "1"
        expected_intent = "request_translation"

        validated_intent = validate_llm_response(response, self.intents)

        assert validated_intent == expected_intent

    def test_validate_llm_response_invalid(self):
        response = "3"
        expected_intent = "invalid_intent"

        validated_intent = validate_llm_response(response, self.intents)

        assert validated_intent == expected_intent

    def test_validate_llm_response_empty_intents(self):
        response = "1"
        intents = []
        expected_intent = "invalid_intent"

        validated_intent = validate_llm_response(response, intents)

        assert validated_intent == expected_intent

    @patch('src.intent_identification_service.IdentifiedIntent')
    @patch('src.intent_identification_service.logger')
    def test_validate_llm_response_invalid_response(
            self, mock_logger, mock_identified_intent):
        error_title = "ValidationError"
        error_type = "json_type"
        error_input = {"response": "invalid_response"}

        mock_identified_intent.side_effect = generate_validation_error(
                title=error_title,
                error_type=error_type,
                input_data=error_input,
        )

        response = "invalid_response"
        expected_intent = "invalid_intent"

        validated_intent = validate_llm_response(response, self.intents)

        assert mock_logger.error.call_count == 1
        mock_logger.error.assert_called_with(
                "Failed to validate LLM response: invalid_response")
        assert validated_intent == expected_intent
