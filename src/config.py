import os
from datetime import datetime, timedelta

LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "amazon")
AWS_CREDENTIAL_NAME: str = os.environ.get("AWS_CREDENTIAL_NAME", "default")

BEDROCK_REGION: str = os.environ.get("BEDROCK_REGION", "us-west-2")
BEDROCK_SERVICE: str = "bedrock-runtime"
BEDROCK_API_PAYLOAD_CONTENT_TYPE: str = "application/json"
BEDROCK_API_PAYLOAD_ACCEPT: str = "application/json"

# The model IDs for different LLM models.
MIXTRAL_8X7B_MODEL_ID: str = "mistral.mixtral-8x7b-instruct-v0:1"
MISTRAL_7B_MODEL_ID: str = "mistral.mistral-7b-instruct-v0:2"
LLAMA_3_7B_MODEL_ID: str = "meta.llama3-8b-instruct-v1:0"
LLAMA_3_70B_MODEL_ID: str = "meta.llama3-70b-instruct-v1:0"

# Selected LLM
LLM_MODEL_ID: str = os.environ.get("LLM_MODEL_ID", LLAMA_3_70B_MODEL_ID)
ALTERNATE_LLM_MODEL_ID: str = (
    os.environ.get("ALTERNATE_LLM_MODEL_ID", MIXTRAL_8X7B_MODEL_ID))

# The maximum number of tokens to generate.
# Lower values will make the model less likely to produce irrelevant text.
MAX_TOKEN_OUTPUT_FOR_INTENT: int = 1
MAX_TOKEN_OUTPUT_FOR_PARSING: int = 200

# The temperature parameter controls the randomness of the output.
# Lower values will make the model more deterministic and repetitive,
# while higher values will make the model more creative and unpredictable.
# The value should be between 0.0 and 1.0.
LLM_TEMPERATURE: float = float(os.environ.get("LLM_TEMPERATURE", 0.0))

# The top_p parameter controls the model's cumulative probability cutoff.
# A lower top_p value (e.g., 0.1) will make the model’s output more
# deterministic and focused on high-probability predictions.
# The value should be between 0.0 and 1.0.
LLM_TOP_P: float = float(os.environ.get("LLM_TOP_P", 0.4))

# The top_k parameter controls the number of highest probability predictions
# that the model considers when generating an output.
# A lower top_k value (e.g., 50) will limit the model’s predictions to the
# top k most likely outcomes.
# The value should be an integer greater than 0.
LLM_TOP_K: int = int(os.environ.get("LLM_TOP_K", 5))

# The keyword arguments for the LLM model for intent identification.
LLAMA_INTENT_KWARGS: dict = {
    "temperature": LLM_TEMPERATURE,
    "max_gen_len": MAX_TOKEN_OUTPUT_FOR_INTENT,
    "top_p": LLM_TOP_P
}

MISTRAL_INTENT_KWARGS = {
    "temperature": LLM_TEMPERATURE,
    "max_tokens": MAX_TOKEN_OUTPUT_FOR_INTENT,
    "top_p": LLM_TOP_P,
    "top_k": LLM_TOP_K,
}

# The keyword arguments for the LLM model for parsing data.
LLAMA_PARSING_KWARGS: dict = {
    "temperature": LLM_TEMPERATURE,
    "max_gen_len": MAX_TOKEN_OUTPUT_FOR_PARSING,
    "top_p": LLM_TOP_P
}

MISTRAL_PARSING_KWARGS = {
    "temperature": LLM_TEMPERATURE,
    "max_tokens": MAX_TOKEN_OUTPUT_FOR_PARSING,
    "top_p": LLM_TOP_P,
    "top_k": LLM_TOP_K,
}

SYSTEM_INTENT_PROMPT: str = """
You are an assistant that detects the intent of incoming email inquiries
for a translation agency. Your task is to classify the incoming emails
based on the content of the emails.

First, identify if the sender is a interpreter or a customer. If identified as
interpreter, select the intent closest to "other". If customer, find the most
relevant intent from the given intent list first before defaulting to "other".

Below are the possible intents with brief descriptions. Use these to
accurately categorise the provided conversation. Respond only with the integer
representing the identified intent ID. Do not include any additional text.


<Output format>
identified_intent_id
</Output format>
"""

current_date_time = (datetime.now() +
                     timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

SYSTEM_PARSING_PROMPT: str = f"""
You are customer support assistant that extracts data from incoming emails.
You will receive an email conversation between a customer and a customer
support agent, as well as a list of parameters to extract from the email.

Given the email and the list of parameters, extract the values of the
parameters from the email and output them in the format specified below. Do
not extract any information from the sender's signature unless explicitly
requested.

If a specific parameter is not present in the email, output null (not a
string) for that parameter. The total number of provided parameters must
match the number of key-value pairs in the output.

If translation between two languages is requested, extract the one that is not
Swedish.

If the email is a request for booking an interpretation session, the date must
be set to a date and time in the future. Today's date and time is
{current_date_time}.

Respond only in the output format specified below, and do not include any
additional text. Prioritise accuracy; if you are unsure about a parameter,
output null. """ + """

<Output format>
{{"given_intent_parameter_key_1": "identified_value_1", ...,
"given_intent_parameter_key_n": "identified_value_n"}}
</Output format>"""

MISTRAL_INSTRUCT_TEMPLATE: str = """
[INST]{system_prompt}
{user_prompt}[/INST]
"""

LLAMA_INSTRUCT_TEMPLATE: str = """
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

USER_INTENT_PROMPT: str = """
<Intents>
{intent_list}
</Intents>

<Email Conversation>
{email_conversation}
</Email Conversation>"""

USER_PARSING_PROMPT: str = """
<Intent Parameters>
{intent_parameters}
</Intent Parameters>

<Email Conversation>
{email_conversation}
</Email Conversation>"""


# The prompt templates for the LLMs.
LLAMA_INTENT_PROMPT_TEMPLATE = LLAMA_INSTRUCT_TEMPLATE.format(
        system_prompt=SYSTEM_INTENT_PROMPT,
        user_prompt=USER_INTENT_PROMPT
)

MISTRAL_INTENT_PROMPT_TEMPLATE = MISTRAL_INSTRUCT_TEMPLATE.format(
        system_prompt=SYSTEM_INTENT_PROMPT,
        user_prompt=USER_INTENT_PROMPT
)

LLAMA_PARSING_PROMPT_TEMPLATE = LLAMA_INSTRUCT_TEMPLATE.format(
        system_prompt=SYSTEM_PARSING_PROMPT,
        user_prompt=USER_PARSING_PROMPT
)

MISTRAL_PARSING_PROMPT_TEMPLATE = MISTRAL_INSTRUCT_TEMPLATE.format(
        system_prompt=SYSTEM_PARSING_PROMPT,
        user_prompt=USER_PARSING_PROMPT
)

SMART_DRAFT_BASE_URL: str = os.environ.get("SMART_DRAFT_BASE_URL",
                                           "http://localhost:8000")

SMART_DRAFT_DETECT_INTENT_ENDPOINT: str = ("/conversations/{"
                                           "conversation_id}/intent-detected")

SMART_DRAFT_VALIDATION_ENDPOINT: str = "/intents/{intent}/validate"

SMART_DRAFT_EXECUTE_ENDPOINT: str = "/intents/{intent}/execute"
