from pydantic import ValidationError  # type: ignore
from pydantic_core import InitErrorDetails  # type: ignore


def generate_validation_error(
        title: str, error_type: str, input_data: dict) -> ValidationError:
    return ValidationError.from_exception_data(
            title=title, line_errors=[
                InitErrorDetails(
                        type=error_type,
                        input=input_data
                )
            ]
    )


VALID_BOOKING_REQUEST_MESSAGE_1 = {
    "sender": "sender@example.com",
    "recipient": "recipient@example.com",
    "subject": "Tolkbokning - Arabiska",
    "role": "user",
    "message": """Hej!

Jag hoppas att du har det bra.

Jag skulle vilja boka en tolk och önskar följande uppgifter noteras för
bokningen. Tolken med ID 234234 skulle föredras för detta uppdrag. Vi
behöver tolkning på arabiska omgående. Tolkningen är
beräknad att vara i en timme och kommer att äga rum i form av platstolkning.

Vänligen notera att bokningen görs i namn av Goei och referensperson är Dr
Hesen Sahin. Adressen för tolkningen är Vänortsstråket 80 A, 232 37
Stockholm, Sverige, och mitt kundnummer är 731264. Tolken ombeds att anmäla
sig i receptionen på bottenplan vid ankomst.

Tack så mycket för hjälpen!

Med vänlig hälsning

Sven Karlberg
"""
}

VALID_TRANSLATION_REQUEST_MESSAGE = {
    "sender": "sender@example.com",
    "recipient": "recipient@example.com",
    "subject": "Översättningsuppdrag - Engelska till Svenska",
    "role": "user",
    "message": """Hej,

Jag undrar om ni kan hjälpa mig att översätta ett juridiskt dokument från
svenska till engelska. Dokumentet är ungefär 15 sidor långt och jag behöver
den färdiga översättningen senast om två veckor. Kan ni även ange ungefärlig
kostnad och hur jag går tillväga för att beställa översättningen? Tack på
förhand för er hjälp.

Med vänliga hälsningar,

Anna Karlsson
"""
}

VALID_MESSAGE_LIST = [VALID_BOOKING_REQUEST_MESSAGE_1]

VALID_INTENTS = [
    {
        "id": 1,
        "slug": "create-text-translation",
        "description": "Kunden vill beställa en översättning."
    },
    {
        "id": 2,
        "slug": "create-booking",
        "description": "Kunden vill boka en tolk."
    },
    {
        "id": 3,
        "slug": "pricing_inquiry",
        "description": "Kunden har frågor om priser."
    },
    {
        "id": 4,
        "slug": "technical_support",
        "description": "Kunden har tekniska problem."
    },
    {
        "id": 5,
        "slug": "complaint",
        "description": "Kunden är missnöjd / lämnar in ett klagomål."
    },
    {
        "id": 6,
        "slug": "other",
        "description": "Kundens förfrågan faller inte direkt in i någon av "
                       "ovanstående kategorier."
    }
]

VALID_DATA_PARAMETERS = [
    {
        "key": "customer_id",
        "data_type": "integer",
        "description": "Set the provided customer's ID here"
    },
    {
        "key": "duration",
        "data_type": "integer",
        "description": "Set the provided duration of the interpretation "
                       "session in minutes."
    },
    {
        "key": "date",
        "data_type": "date",
        "description": "Set the provided date of the interpretation session. "
                       "If the request is for an emergency booking, set the "
                       "date to the current date. Format: YYYY-MM-DD"
    },
    {
        "key": "time",
        "data_type": "time",
        "description": "Set the provided time of the interpretation session. "
                       "If the request is for an emergency booking, set the "
                       "time to the current time. Format: HH:MM"
    },
    {
        "key": "type",
        "data_type": "string",
        "description": "Set the type of the booking. Valid options are: "
                       "physical, video, convey, phone. Set to phone if "
                       "neither address nor video provider is explicitly "
                       "provided."
    },
    {
        "key": "is_immediate",
        "data_type": "boolean",
        "description": "Set to true if it is an emergency booking, otherwise "
                       "set to false."
    },
    {
        "key": "language",
        "data_type": "string",
        "description": "Set to the ISO 639-2 of the specified language, e.g., "
                       "ara for Arabic, som for Somali, prs for Dari."
    },
    {
        "key": "convey_message",
        "data_type": "string",
        "description": "Set to the provided message to convey. Requires type "
                       "to be convey."
    },
    {
        "key": "convey_phone",
        "data_type": "string",
        "description": "Set to the provided phone number to the recipient of "
                       "the convey message. Requires type to be convey."

    },
    {
        "key": "video_provider",
        "data_type": "string",
        "description": "Set to the provided video provider. Valid options "
                       "are: skype, jitsi, google_meet, ms_teams, "
                       "visba_care, zoom, clinic, dt_mote, other. Requires "
                       "type to be video."
    },
    {
        "key": "address",
        "data_type": "string",
        "description": "Set to the provided address for the interpretation "
                       "session. Requires type to be physical."
    },
    {
        "key": "city",
        "data_type": "string",
        "description": "Set to the provided city for the interpretation "
                       "session. Requires type to be physical."
    }
]
