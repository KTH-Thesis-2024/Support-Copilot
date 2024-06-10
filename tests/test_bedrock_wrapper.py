from unittest.mock import MagicMock, patch

import pytest

from src.bedrock_wrapper import (prompt_llm, setup_bedrock_client, setup_llm,
                                 setup_model_kwargs)
from src.config import (BEDROCK_REGION, BEDROCK_SERVICE, LLAMA_INTENT_KWARGS,
                        LLAMA_PARSING_KWARGS, LLM_MODEL_ID,
                        MISTRAL_INTENT_KWARGS, MISTRAL_PARSING_KWARGS)


class TestPromptLLM:
    @pytest.fixture
    def llm_client(self):
        return MagicMock(invoke=MagicMock(return_value='LLM response'))

    @pytest.fixture
    def setup_bedrock_client_mock(self):
        with patch('src.bedrock_wrapper.setup_bedrock_client',
                   return_value=None) as mock:
            yield mock

    @pytest.fixture
    def setup_llm_mock(self, llm_client):
        with patch('src.bedrock_wrapper.setup_llm',
                   return_value=llm_client) as mock:
            yield mock

    @pytest.mark.parametrize("change_llm", [True, False])
    def test_prompt_llm(
            self, setup_bedrock_client_mock, setup_llm_mock, llm_client,
            change_llm):

        prompt = "formatted prompt"
        operation_type = 'random_operation_type'
        expected_llm_response = 'LLM response'

        response = prompt_llm(prompt, operation_type, change_llm=change_llm)

        setup_bedrock_client_mock.assert_called_once()
        if change_llm:
            setup_llm_mock.assert_called_once_with(
                    None,
                    operation_type=operation_type,
                    alternate_model=True)
        else:
            setup_llm_mock.assert_called_once_with(
                    None,
                    operation_type=operation_type)
        llm_client.invoke.assert_called_once_with(prompt)
        assert response == expected_llm_response


class TestSetupBedrockClient:
    @pytest.fixture
    def mock_bedrock_client(self):
        with patch('src.bedrock_wrapper.boto3.client') as mock:
            yield mock

    def test_setup_bedrock_client_success(self, mock_bedrock_client):
        bedrock_client = setup_bedrock_client()

        mock_bedrock_client.assert_called_once_with(
                service_name=BEDROCK_SERVICE,
                region_name=BEDROCK_REGION)
        assert bedrock_client == mock_bedrock_client.return_value

    def test_setup_bedrock_client_failure(self, mock_bedrock_client):
        mock_bedrock_client.side_effect = Exception("Connection error")

        with pytest.raises(RuntimeError) as exc_info:
            setup_bedrock_client()

        assert str(exc_info.value) == (
            "Failed to setup Bedrock client: Connection error")


class TestSetupLLM:
    model_kwargs = {'some': 'kwargs'}

    @pytest.fixture
    def bedrock_client(self):
        return MagicMock()

    @pytest.fixture
    def setup_model_kwargs_mock(self):
        with patch('src.bedrock_wrapper.setup_model_kwargs',
                   return_value=self.model_kwargs) as mock:
            yield mock

    @pytest.fixture
    def bedrock_llm_mock(self):
        with patch('src.bedrock_wrapper.BedrockLLM') as mock:
            yield mock

    def test_setup_llm_success(
            self, bedrock_client, setup_model_kwargs_mock, bedrock_llm_mock):
        operation_type = "intent"

        llm_instance = setup_llm(bedrock_client, operation_type)

        setup_model_kwargs_mock.assert_called_once_with(
                LLM_MODEL_ID, operation_type)
        bedrock_llm_mock.assert_called_once_with(
                client=bedrock_client,
                model_id=LLM_MODEL_ID,
                model_kwargs=self.model_kwargs)
        assert llm_instance == bedrock_llm_mock.return_value

    def test_setup_llm_exception_handling(
            self, bedrock_client, setup_model_kwargs_mock, bedrock_llm_mock):
        bedrock_llm_mock.side_effect = Exception("Connection failure")

        with pytest.raises(RuntimeError) as exc_info:
            setup_llm(bedrock_client, "intent")

        assert ("Failed to setup Bedrock: Connection failure"
                in str(exc_info.value))
        bedrock_llm_mock.assert_called_once_with(
                client=bedrock_client,
                model_id=LLM_MODEL_ID,
                model_kwargs=self.model_kwargs)


class TestSetupModelKwargs:
    @pytest.mark.parametrize("model_id, operation_type, expected", [
        ("mistral", "intent", MISTRAL_INTENT_KWARGS),
        ("mistral", "parsing", MISTRAL_PARSING_KWARGS),
        ("llama", "intent", LLAMA_INTENT_KWARGS),
        ("llama", "parsing", LLAMA_PARSING_KWARGS),
    ])
    def test_success(self, model_id, operation_type, expected):
        assert setup_model_kwargs(model_id, operation_type) == expected

    def test_mistral_invalid_operation(self):
        with pytest.raises(ValueError) as exc_info:
            setup_model_kwargs("mistral", "typing")

        assert str(exc_info.value) == "Invalid operation type."

    def test_llama_invalid_operation(self):
        with pytest.raises(ValueError) as exc_info:
            setup_model_kwargs("llama", "translation")

        assert str(exc_info.value) == "Invalid operation type."

    def test_invalid_model_id(self):
        with pytest.raises(ValueError) as exc_info:
            setup_model_kwargs("unicorn", "intent")

        assert str(exc_info.value) == "Invalid model ID."
