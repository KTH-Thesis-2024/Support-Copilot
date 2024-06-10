from typing import Optional

import requests  # type: ignore

from src import logger
from src.config import (SMART_DRAFT_BASE_URL,
                        SMART_DRAFT_DETECT_INTENT_ENDPOINT,
                        SMART_DRAFT_VALIDATION_ENDPOINT,
                        SMART_DRAFT_EXECUTE_ENDPOINT)


def send_intent_response(conversation_id: int, identified_intent: str) -> None:
    endpoint_url = generate_api_endpoint(
            "intent-detection", conversation_id=conversation_id)
    try:
        response = requests.put(
                url=endpoint_url,
                json={"detected_intent": identified_intent})

        response.raise_for_status()
        logger.info("Intent response successfully sent.")

    except requests.RequestException as error:
        logger.error(f"Failed to send intent response: {error}")
        raise RuntimeError(f"Failed to send intent response: {error}")


def send_validation_response(
        intent: str, identified_params: dict, conversation_id: int) -> None:
    endpoint_url = generate_api_endpoint("validation", intent=intent)
    try:
        response = requests.post(url=endpoint_url, json=identified_params)

        response.raise_for_status()
        logger.info("Parsed validation successfully sent.")

        response_data = response.json()
        missing_parameters = response_data['data']['missing_parameters']

        if missing_parameters:
            logger.info("Missing parameters detected.")
            send_execution_response(intent, identified_params,
                                    conversation_id, missing_parameters=True)

        else:
            logger.info("No missing parameters detected.")
            send_execution_response(
                    intent, identified_params, conversation_id)

    except requests.RequestException as error:
        logger.error(f"Failed to send validation response: {error}")
        raise RuntimeError(f"Failed to send validation response: {error}")


def send_execution_response(
        intent: str, identified_params: dict, conversation_id: int,
        missing_parameters: bool = False) -> None:
    endpoint_url = generate_api_endpoint("execution", intent=intent)

    json_payload = {
        "conversation_id": conversation_id,
        "payload": identified_params,
        "generated_response": "Incomplete, but we don't care, do we?" if
        missing_parameters else "Complete."
    }

    try:
        response = requests.post(url=endpoint_url, json=json_payload)
        response.raise_for_status()

        logger.info("Execution response successfully sent.")

    except requests.RequestException as error:
        logger.error(f"Failed to send execution response: {error}")
        raise RuntimeError(f"Failed to send execution response: {error}")


def generate_api_endpoint(endpoint: str, intent: Optional[str] = None,
                          conversation_id: Optional[int] = None) -> str:
    if endpoint == "intent-detection":
        endpoint_part = (SMART_DRAFT_DETECT_INTENT_ENDPOINT
                         .format(conversation_id=conversation_id))
    elif endpoint == "validation":
        endpoint_part = (SMART_DRAFT_VALIDATION_ENDPOINT
                         .format(intent=intent))
    elif endpoint == "execution":
        endpoint_part = (SMART_DRAFT_EXECUTE_ENDPOINT
                         .format(intent=intent))
    else:
        raise ValueError("Invalid endpoint specified.")

    full_url = SMART_DRAFT_BASE_URL + endpoint_part
    logger.debug(f"Generated endpoint URL for {endpoint}: {full_url}")
    return full_url
