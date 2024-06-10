import re
from typing import List

from langchain_core.prompts import PromptTemplate  # type: ignore
from pydantic import ValidationError  # type: ignore

from src import logger
from src.bedrock_wrapper import prompt_llm
from src.config import LLAMA_INTENT_PROMPT_TEMPLATE, LLM_MODEL_ID, \
    MISTRAL_INTENT_PROMPT_TEMPLATE
from src.models import IdentifiedIntent, Intent, IntentRequest


def identify_intent(intent_request: IntentRequest) -> str:
    prompt: str = generate_prompt(intent_request)
    llm_response: str = prompt_llm(prompt, operation_type="intent")
    identified_intent: str = validate_llm_response(llm_response,
                                                   intent_request.intents)

    if identified_intent != "invalid_intent":
        logger.info("Initial intent identification successful.")
        return identified_intent

    logger.info("Initial intent identification failed. Retrying with alternate"
                " configuration.")
    llm_response = prompt_llm(
            prompt, operation_type="intent", change_llm=True)
    identified_intent = validate_llm_response(llm_response,
                                              intent_request.intents)

    if identified_intent != "invalid_intent":
        logger.info("Intent identification successful after retry.")
        return identified_intent

    else:
        logger.info("Failed to identify a valid intent after retry.")
        return identified_intent


def generate_prompt(intent_request: IntentRequest) -> str:
    intents: str = intent_request.output_stringified_intents()
    messages: str = intent_request.output_stringified_messages()

    prompt_template: PromptTemplate = PromptTemplate(
            template=(MISTRAL_INTENT_PROMPT_TEMPLATE
                      if "mistral" in LLM_MODEL_ID
                      else LLAMA_INTENT_PROMPT_TEMPLATE),
            input_variables=["intent_list", "email_conversation"]
    )

    prompt: str = prompt_template.format(
            intent_list=intents,
            email_conversation=messages
    )

    logger.info("Prompt generated for LLM processing.")
    return prompt


def validate_llm_response(response: str, intents: List[Intent]) -> str:
    logger.debug(f"Validating LLM response: {response}")
    try:
        response = extract_integer(response)
        identified_intent: IdentifiedIntent = IdentifiedIntent(
                intent_id=response)  # type: ignore

        for intent in intents:
            if intent.id == identified_intent.intent_id:
                return intent.slug

    except ValidationError:
        logger.error(f"Failed to validate LLM response: {response}")
        return "invalid_intent"

    logger.error(f"Failed to identify a valid intent: {response}")
    return "invalid_intent"


def extract_integer(input_string) -> str:
    match = re.search(r'\d+', input_string)
    return match.group(0) if match else "invalid_response"
