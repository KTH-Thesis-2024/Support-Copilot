from typing import Optional

import boto3  # type: ignore
from langchain_aws import BedrockLLM  # type: ignore

from src import logger
from src.config import (ALTERNATE_LLM_MODEL_ID, BEDROCK_REGION,
                        BEDROCK_SERVICE, LLAMA_INTENT_KWARGS,
                        LLAMA_PARSING_KWARGS, LLM_MODEL_ID,
                        MISTRAL_INTENT_KWARGS, MISTRAL_PARSING_KWARGS)


def prompt_llm(
        prompt: str, operation_type: str, change_llm: bool = False) -> str:
    bedrock_client: boto3.client = setup_bedrock_client()
    llm: BedrockLLM

    if change_llm:
        llm = setup_llm(bedrock_client,
                        alternate_model=True,
                        operation_type=operation_type)
    else:
        llm = setup_llm(bedrock_client,
                        operation_type=operation_type)

    response: str = llm.invoke(prompt)
    logger.info("Prompting successful.")
    return response


def setup_bedrock_client() -> boto3.client:
    logger.debug("Setting up the Bedrock client.")
    try:
        bedrock_client: boto3.client = boto3.client(
                service_name=BEDROCK_SERVICE,
                region_name=BEDROCK_REGION
        )

        logger.info("Bedrock client successfully set up.")
        return bedrock_client

    except Exception as error:
        logger.error(f"Failed to setup Bedrock client: {str(error)}")
        raise RuntimeError(f"Failed to setup Bedrock client: {str(error)}")


def setup_llm(bedrock_client: boto3.client,
              operation_type: str,
              alternate_model: Optional[bool] = False) -> BedrockLLM:
    model_id: str = ALTERNATE_LLM_MODEL_ID if alternate_model else LLM_MODEL_ID
    model_kwargs: dict = setup_model_kwargs(model_id, operation_type)

    try:
        llm: BedrockLLM = BedrockLLM(
                client=bedrock_client,
                model_id=model_id,
                model_kwargs=model_kwargs
        )

        logger.info("Bedrock client successfully set up.")
        return llm

    except Exception as error:
        logger.error(f"Failed to setup Bedrock: {str(error)}")
        raise RuntimeError(f"Failed to setup Bedrock: {str(error)}")


def setup_model_kwargs(model_id: str, operation_type: str) -> dict:
    if "mistral" in model_id:
        if operation_type == "intent":
            return MISTRAL_INTENT_KWARGS
        elif operation_type == "parsing":
            return MISTRAL_PARSING_KWARGS
        else:
            raise ValueError("Invalid operation type.")

    elif "llama" in model_id:
        if operation_type == "intent":
            return LLAMA_INTENT_KWARGS
        elif operation_type == "parsing":
            return LLAMA_PARSING_KWARGS
        else:
            raise ValueError("Invalid operation type.")

    raise ValueError("Invalid model ID.")
