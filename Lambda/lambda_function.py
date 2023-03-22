### Required Libraries ###
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")

def parse_risk_level(risk_level):
    if str.lower(risk_level)=='none':
        bonds=100
        equities=0
    if str.lower(risk_level)=='low':
        bonds=60
        equities=40
    if str.lower(risk_level)=='medium':
        bonds=40
        equities=60
    if str.lower(risk_level)=='high':
        bonds=20
        equities=80
    return {'bonds':bonds,'equities':equities}

def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


"""
Step 3: Enhance the Robo Advisor with an Amazon Lambda Function

In this section, you will create an Amazon Lambda function that will validate the data provided by the user on the Robo Advisor.

1. Start by creating a new Lambda function from scratch and name it `recommendPortfolio`. Select Python 3.7 as runtime.

2. In the Lambda function code editor, continue by deleting the AWS generated default lines of code, then paste in the starter code provided in `lambda_function.py`.

3. Complete the `recommend_portfolio()` function by adding these validation rules:

    * The `age` should be greater than zero and less than 65.
    * The `investment_amount` should be equal to or greater than 5000.

4. Once the intent is fulfilled, the bot should respond with an investment recommendation based on the selected risk level as follows:

    * **none:** "100% bonds (AGG), 0% equities (SPY)"
    * **low:** "60% bonds (AGG), 40% equities (SPY)"
    * **medium:** "40% bonds (AGG), 60% equities (SPY)"
    * **high:** "20% bonds (AGG), 80% equities (SPY)"

> **Hint:** Be creative while coding your solution, you can have all the code on the `recommend_portfolio()` function, or you can split the functionality across different functions, put your Python coding skills in action!

5. Once you finish coding your Lambda function, test it using the sample test events provided for this Challenge.

6. After successfully testing your code, open the Amazon Lex Console and navigate to the `recommendPortfolio` bot configuration, integrate your new Lambda function by selecting it in the “Lambda initialization and validation” and “Fulfillment” sections.

7. Build your bot, and test it with valid and invalid data for the slots.

"""


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    slots=get_slots(intent_request)
    validation_result=validate_age_investmentAmount(intent_request)
    source=intent_request['invocationSource']
    if source == 'DialogCodeHook':
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(
                intent_request['sessionAttributes'],
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )
        output_session_attributes=intent_request['sessionAttributes']
        
        
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        if risk_level is not None:
            output_session_attributes['bonds'] = parse_risk_level(risk_level)['bonds']
            output_session_attributes['equities'] = parse_risk_level(risk_level)['equities']
        return delegate(output_session_attributes, get_slots(intent_request))
    
    return close(
        intent_request['sessionAttributes'],
        'Fulfilled',
        {
            'contentType':'PlainText',
            'content':'''We recommend a portfolio of
            {}% bonds (AGG) and {}% equities (SPY)
            '''.format(
                parse_risk_level(risk_level)['bonds'],parse_risk_level(risk_level)['equities']
            )
        }
    )
    
def validate_age_investmentAmount(intent_request):
    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]
    if age is not None:
        age=parse_int(age)
        if age <= 0:
            return build_validation_result(
                False, 
                'age', 
                'Please enter a valid age. Age must be greater than 0'
            )
        elif age > 65:
            return build_validation_result(
                False, 
                'age', 
                "I'm sorry you do not meet our age requirements. Users must be under 65."
            )
    if investment_amount is not None:
        investment_amount=parse_int(investment_amount)
        if investment_amount <= 0:
            return build_validation_result(
                False, 
                'investmentAmount', 
                "Please enter an investment amount greater than 0."
            )
        elif investment_amount < 5000:
            return build_validation_result(
                False, 
                'investmentAmount', 
                "I'm sorry you do not meet our requirement for investment amount. Users must invest at least $5000"
            )
    return build_validation_result(
        True,
        None,
        None
    )

### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
