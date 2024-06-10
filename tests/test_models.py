from src.models import Intent, IntentRequest, Message


def test_message_str():
    message = Message(
            sender='alice@example.com',
            recipient='bob@example.com',
            subject='Meeting',
            role='coordinator',
            message='Discuss the upcoming translation meeting.'
    )

    expected_output = (
        "Sender: alice@example.com, Recipient: bob@example.com \n"
        "Subject: Meeting, Role: coordinator \n"
        "Message: Discuss the upcoming translation meeting.\n"
    )

    assert str(message) == expected_output


def test_intent_str():
    intent = Intent(
            id=1,
            slug='discuss-booking',
            description='Intent to discuss booking.'
    )
    expected_output = ("1 = discuss-booking: Intent to discuss booking.")

    assert str(intent) == expected_output


def test_output_stringified_messages():
    messages = [
        Message(sender='alice@example.com', recipient='bob@example.com',
                subject='Meeting', role='coordinator',
                message='Discuss the upcoming project milestones.'),
        Message(sender='carol@example.com', recipient='dave@example.com',
                subject='Budget', role='finance_manager',
                message='Review budget allocations for next year.')
    ]
    request = IntentRequest(messages=messages, intents=[])
    expected_output = (
        "Sender: alice@example.com, Recipient: bob@example.com \n"
        "Subject: Meeting, Role: coordinator \n"
        "Message: Discuss the upcoming project milestones.\n\n"
        "Sender: carol@example.com, Recipient: dave@example.com \n"
        "Subject: Budget, Role: finance_manager \n"
        "Message: Review budget allocations for next year.\n"
    )
    assert request.output_stringified_messages() == expected_output


def test_output_stringified_intents():
    intents = [
        Intent(id=1, slug='increase-sales',
               description='Intent to boost sales in the next quarter.'),
        Intent(id=2, slug='reduce-costs',
               description='Plan to reduce operational costs by 10%.')

    ]
    request = IntentRequest(messages=[], intents=intents)

    expected_output = (
        "1 = increase-sales: Intent to boost sales in the next quarter.\n"
        "2 = reduce-costs: Plan to reduce operational costs by 10%."
    )
    assert request.output_stringified_intents() == expected_output
