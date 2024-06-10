import json
import re
from datetime import date, time
from typing import Any, Dict, Optional

from langchain_core.prompts import PromptTemplate  # type: ignore
from pydantic import (BaseModel, Field, ValidationError,  # type: ignore
                      create_model)  # type: ignore

from src import logger
from src.bedrock_wrapper import prompt_llm
from src.config import LLAMA_PARSING_PROMPT_TEMPLATE, LLM_MODEL_ID, \
    MISTRAL_PARSING_PROMPT_TEMPLATE
from src.models import ExtractRequest


def extract_data(parse_request: ExtractRequest) -> dict[str, Any]:
    prompt: str = generate_prompt(parse_request)
    llm_response: str = prompt_llm(prompt, operation_type="parsing")
    validated_parameters: Dict[str, Any] = validate_llm_response(
            llm_response, parse_request)

    if "error" not in validated_parameters:
        logger.debug(f"Identified parameters: {validated_parameters}")
        logger.info("Initial parsing successful.")
        return validated_parameters

    logger.info(
        "Initial parsing failed. Retrying with alternate configuration.")
    llm_response = prompt_llm(
            prompt, operation_type="parsing", change_llm=True)
    validated_parameters = validate_llm_response(llm_response,
                                                 parse_request)

    if "error" not in validated_parameters:
        logger.info("Parsing successful after retry.")
        return validated_parameters

    else:
        logger.debug("Failed to identify a valid intent after retry. "
                     f"Parameters: {validated_parameters}")
        logger.info("Failed to identify a valid intent after retry.")
        return validated_parameters


def generate_prompt(parse_request: ExtractRequest) -> str:
    logger.debug("Generating prompt for LLM.")
    intent_params: str = parse_request.output_stringified_data_parameters()
    messages: str = parse_request.output_stringified_messages()

    prompt_template: PromptTemplate = PromptTemplate(
            template=(
                MISTRAL_PARSING_PROMPT_TEMPLATE if "mistral" in LLM_MODEL_ID
                else LLAMA_PARSING_PROMPT_TEMPLATE),
            input_variables=["intent_parameters", "email_conversation"]
    )

    prompt: str = prompt_template.format(
            intent_parameters=intent_params,
            email_conversation=messages
    )

    logger.debug(f"Generated prompt: {prompt}")
    logger.info("Prompt generated for LLM processing.")
    return prompt


def validate_llm_response(
        response: str, extract_request: ExtractRequest) -> dict[str, Any]:
    ValidationModel: BaseModel = generate_dynamic_model(extract_request)
    dynamic_model = ValidationModel()  # type: ignore
    try:
        if "\n" in response:
            response = response.replace("\n", "")

        response = extract_json_like_content(response)
        llm_response_dict: dict = json.loads(response)

        for field_name in dynamic_model.model_fields.keys():
            try:
                if field_name in llm_response_dict:
                    setattr(dynamic_model, field_name,
                            llm_response_dict[field_name])
            except ValidationError:
                setattr(dynamic_model, field_name, None)

        logger.info("LLM response validated.")
        return dynamic_model.model_dump(exclude_none=True)

    except json.JSONDecodeError as error:
        logger.error(f"Failed to validate LLM response: {str(error)}")
        return {"error": f"invalid_response: {response}"}

    except Exception as error:
        logger.error(f"Validation failed: {str(error)}", exc_info=True)
        return {"error": f"invalid_response: {str(error)}"}


def extract_json_like_content(input_string: str) -> str:
    match = re.search(r'\{.*?\}', input_string)

    if not match:
        return input_string

    json_like_content = match.group(0)
    return re.sub(r',\s*}', '}', json_like_content)


def generate_dynamic_model(parse_request: ExtractRequest) -> BaseModel:
    intent_parameters = {
        param.key: param.data_type for param in parse_request.data_parameters
    }

    field_definitions: Dict[str, Any] = {}

    for key, data_type in intent_parameters.items():
        if "int" in data_type.lower():
            field_definitions[key] = (Optional[int], Field(default=None))

        elif "date" in data_type.lower():
            field_definitions[key] = (Optional[date], Field(default=None))

        elif "time" in data_type.lower():
            field_definitions[key] = (Optional[time], Field(default=None))

        elif "bool" in data_type.lower():
            field_definitions[key] = (Optional[bool], Field(default=None))

        else:
            field_definitions[key] = (Optional[str], Field(default=None))

    return create_model('ValidationModel',
                        **field_definitions)  # type: ignore
