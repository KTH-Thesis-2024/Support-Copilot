import json
from unittest.mock import MagicMock, patch

import pytest

from src.s3_wrapper import retrieve_s3_payload


@patch('src.s3_wrapper.boto3.client')
def test_retrieve_s3_payload_success(mock_boto_client):
    bucket_name = "test-bucket"
    object_key = "path/to/object"
    s3_payload_path = f"/{bucket_name}/{object_key}"
    test_data = {
        "intents": [
            {
                "id": 1,
                "slug": "create-booking",
                "description": "Intent to create a booking"
            }
        ],
        "messages": [
            {
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "subject": "Test Subject",
                "role": "user",
                "message": "This is the message body"
            }
        ]
    }

    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps(test_data).encode()

    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client
    mock_client.get_object.return_value = {'Body': mock_body}

    result = retrieve_s3_payload(s3_payload_path)

    assert result == test_data
    mock_client.get_object.assert_called_once_with(
            Bucket=bucket_name, Key=object_key)


@patch('src.s3_wrapper.boto3.client')
def test_retrieve_s3_payload_s3_service_error(mock_boto3_client):
    mock_s3_wrapper = MagicMock()
    mock_s3_wrapper.get_object.side_effect = Exception("Service failure")
    mock_boto3_client.return_value = mock_s3_wrapper

    with pytest.raises(RuntimeError) as exc_info:
        retrieve_s3_payload("/test-bucket/path/to/nonexistent.json")

    assert "Failed to retrieve S3 payload:" in str(exc_info.value)
    assert "AccessDenied" in str(exc_info.value) or "Service failure" in str(
            exc_info.value)


@patch('src.s3_wrapper.boto3.client')
def test_retrieve_s3_payload_invalid_path_format(mock_boto3_client):
    mock_boto3_client.return_value = MagicMock()

    with pytest.raises(ValueError) as exc_info:
        retrieve_s3_payload("incorrect-format-path")

    assert "Invalid S3 payload path." in str(exc_info.value)
    mock_boto3_client.assert_not_called()


@patch('src.s3_wrapper.boto3.client')
def test_retrieve_s3_payload_json_loads_failure(mock_boto_client):
    mock_body = MagicMock()
    mock_body.read.return_value = b'{invalid-json'

    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client
    mock_client.get_object.return_value = {'Body': mock_body}

    with pytest.raises(RuntimeError) as exc_info:
        retrieve_s3_payload("/bucket_name/path/to/file.json")

    assert str(exc_info.value) == "Failed to decode S3 payload."
