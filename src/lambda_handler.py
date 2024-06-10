import json
from typing import Any, Dict

from pydantic import ValidationError  # type: ignore

from src import logger
from src.data_extraction_service import extract_data
from src.intent_identification_service import identify_intent
from src.models import IntentRequest, ExtractRequest, SQSMessage
from src.s3_wrapper import retrieve_s3_payload
from src.smart_draft_api import send_intent_response, send_validation_response


def lambda_handler(event: Dict[str, Any], context: Any):
    logger.info("Lambda function has been invoked.")
    record: Dict[str, Any] = event["Records"][0]
    sqs_payload: Dict[str, Any] = json.loads(record["body"])
    event_source_arn = record["eventSourceARN"]
    conversation_id: int = sqs_payload["conversation_id"]

    try:
        s3_payload: Dict[str, Any] = retrieve_data(sqs_payload)

        if "intent" in event_source_arn.lower():
            logger.info("Processing the intent.")
            handle_intent_request(conversation_id, s3_payload)
            logger.info("Successfully processed the intent.")
        elif "extraction" in event_source_arn.lower():
            logger.info("Processing the extraction request.")
            handle_extraction_request(s3_payload, sqs_payload, conversation_id)
            logger.info("Successfully processed the extraction request.")
        else:
            logger.error(f"Unknown event source ARN: {event_source_arn}.")
            raise Exception("Unknown event source ARN.")

    except ValidationError as error:
        if "intent" in event_source_arn:
            logger.error(f"Failed to parse IntentRequest: {error}")
            send_intent_response(conversation_id, str(error))
        elif "extraction" in event_source_arn:
            logger.error(f"Failed to parse ExtractRequest: {error}")
            validation_error: dict = {"error": str(error)}
            send_validation_response(
                    sqs_payload["intent"], validation_error, conversation_id)

    except Exception as error:
        logger.error(f"Lambda handler encountered an error: {str(error)}")

        if "intent" in event_source_arn:
            send_intent_response(conversation_id, str(error))

        elif "extraction" in event_source_arn:
            error_message: dict = {"error": str(error)}
            send_validation_response(
                    sqs_payload["intent"], error_message, conversation_id)

        else:
            logger.error(f"Failed to handle request : {conversation_id}")


def retrieve_data(sqs_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        sqs_message: SQSMessage = SQSMessage(**sqs_payload)
        s3_payload_path: str = sqs_message.payload_path

        s3_payload: dict[str, Any] = retrieve_s3_payload(s3_payload_path)
        logger.debug("Successfully retrieved S3 payload: "
                     f"{json.dumps(s3_payload)}")

        logger.info("Successfully retrieved S3 payload.")
        return s3_payload
    except ValidationError as error:
        logger.error(f"Failed to parse IntentRequest: {error}")
        raise error


def handle_intent_request(conversation_id: int, s3_payload: Dict[str, Any]):
    intent_request: IntentRequest = IntentRequest(**s3_payload)
    detected_intent: str = identify_intent(intent_request)

    logger.info(f"Detected intent: {detected_intent}")
    send_intent_response(conversation_id, detected_intent)


def handle_extraction_request(
        s3_payload: dict, sqs_payload: Dict[str, Any], conversation_id: int):
    extraction_request: ExtractRequest = ExtractRequest(**s3_payload)
    detected_parameters: Dict[str, Any] = extract_data(extraction_request)
    intent: str = sqs_payload["intent"]

    logger.info(f"Detected parameters: {json.dumps(detected_parameters)}")
    send_validation_response(intent, detected_parameters, conversation_id)
