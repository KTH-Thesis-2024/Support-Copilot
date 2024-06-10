import json
from unittest.mock import patch

import pytest

from src.data_extraction_service import generate_prompt, extract_data
from src.models import DataParameter, Message, ExtractRequest
from tests.test_utilites import VALID_DATA_PARAMETERS, VALID_MESSAGE_LIST

parse_request = ExtractRequest(
        messages=[Message(**VALID_MESSAGE_LIST[0])],
        data_parameters=[
            DataParameter(**params) for params in VALID_DATA_PARAMETERS
        ]
)


class TestProcessParsing:
    @pytest.fixture
    def mock_bedrock_llm(self):
        with patch("src.bedrock_wrapper.BedrockLLM") as mock_bedrock_llm:
            yield mock_bedrock_llm

    def test_process_parsing_successful(self, mock_bedrock_llm):
        valid_response = {'address': 'Vänortsstråket 80 A',
                          'city': 'Stockholm',
                          'customer_id': '234234',
                          'date': '2023-04-03',
                          'duration': '60',
                          'is_immediate': False,
                          'language': 'ara',
                          'time': '14:20:00',
                          'type': 'physical'}

        mock_bedrock_llm.return_value.invoke.return_value = json.dumps(
                valid_response)

        result = extract_data(parse_request)

        assert result == valid_response

    def test_process_parsing_invalid_intent_retry_success(
            self, mock_bedrock_llm):
        invalid_response = "{'incorrect_json': 'format'"
        expected_response = {
            'error': "invalid_response: {'incorrect_json': 'format'"}

        mock_bedrock_llm.return_value.invoke.return_value = invalid_response

        result = extract_data(parse_request)

        assert result == expected_response


class TestGeneratePrompt:
    def test_generate_prompt(self):
        simple_parse_request = ExtractRequest(
                messages=[
                    Message(
                            sender="customer",
                            recipient="agent",
                            role="user",
                            message="Test message",
                    )
                ],
                injected_data=[],
                data_parameters=[
                    DataParameter(
                            key="Test key",
                            data_type="string",
                            description="Test description",
                    )
                ]
        )

        prompt = generate_prompt(simple_parse_request)

        assert "Test message" in prompt
        assert "Test key" in prompt
