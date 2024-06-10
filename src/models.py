from typing import List

from pydantic import BaseModel, Field  # type: ignore


class SQSMessage(BaseModel):
    conversation_id: int = Field(
            ..., description='The identifier of the conversation.')
    message_type: str = Field(
            ..., description='The type of conversation; chat or email.')
    payload_path: str = Field(
            ..., description='The path to the payload file.')


class Message(BaseModel):
    sender: str = Field(
            ..., description='Email address of the sender.')
    recipient: str = Field(
            ..., description='Email address of the recipient.')
    subject: str = Field(
            None, description='The subject line of the message.')
    role: str = Field(
            ..., description='The role of the message sender.')
    message: str = Field(
            ..., description='The content body of the message.')

    def __str__(self):
        return f"Sender: {self.sender}, Recipient: {self.recipient} \n" \
               f"Subject: {self.subject}, Role: {self.role} \n" \
               f"Message: {self.message}\n"


class Intent(BaseModel):
    id: int = Field(
            ..., description='The identifier of the intent.')
    slug: str = Field(
            ..., description='An intent that the sender might have.')
    description: str = Field(
            ..., description='The description of the intent.')

    def __str__(self):
        return f"{self.id} = {self.slug}: {self.description}"


class IntentRequest(BaseModel):
    messages: list[Message] = Field(
            ..., description='A list of messages to analyze.')
    intents: list[Intent] = Field(
            ..., description='List of intents to utilise for analysis.')

    def output_stringified_messages(self):
        return "\n".join([str(message) for message in self.messages])

    def output_stringified_intents(self):
        return "\n".join([str(intent) for intent in self.intents])


class IdentifiedIntent(BaseModel):
    intent_id: int = Field(
            ..., description='The id of the identified intent.')


class DataParameter(BaseModel):
    key: str = Field(
            ..., description='The key of the intent parameter.')
    data_type: str = Field(
            ..., description='The data type of the intent parameter.')
    description: str = Field(
            ..., description='The description of the intent parameter.')

    def __str__(self):
        return (
            f"{self.key} [{self.data_type}]: {self.description}"
        )


class ExtractRequest(BaseModel):
    messages: List[Message] = Field(
            ..., description='A list of messages to analyze.')
    data_parameters: List[DataParameter] = Field(
            ...,
            description='List of parameters to extract.')

    def output_stringified_messages(self):
        return "\n".join(map(str, self.messages))

    def output_stringified_data_parameters(self):
        return "\n".join(map(str, self.data_parameters))
