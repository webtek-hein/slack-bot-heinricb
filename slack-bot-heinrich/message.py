import threading
import time
import re
from slackclient import SlackClient
import tweepy
import config

# instantiate Slack client
slack_client = SlackClient(config.API_token)
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
auth.set_access_token(config.ACCESS_TOKEN,
                      config.ACCESS_SECRET)

api = tweepy.API(auth)

trendsList = api.trends_place(1)
# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "post"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"



def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)
    listStr = "Here are the top 10 trending tweets worldwide: \n"

    # Finds and executes the given command, filling in response
    response = None
    if command.lower() in EXAMPLE_COMMAND:
        trends = trendsList[0]['trends']
        payload = []
        for i in trends:
            if i['tweet_volume'] != None:
                payload.append([i['tweet_volume'], i['name']])
        payload.sort(reverse=True)
        counter = 1

        for j in payload:
            if counter <= 10:
                listStr += str(counter)+'. ' + j[1] + "\n"
                counter += 1
            else:
                break
        response = listStr

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )
def timelypost():
    listStr = "Here are the top 10 trending tweets worldwide: \n"

     # Sends the response back to the channel
    trends = trendsList[0]['trends']
    payload = []
    response=''
    for i in trends:
        if i['tweet_volume'] != None:
            payload.append([i['tweet_volume'], i['name']])
        payload.sort(reverse=True)
        counter = 1

        for j in payload:
            if counter <= 10:
                listStr += str(counter)+'. ' + j[1] + "\n"
                counter += 1
            else:
                break
        response = listStr
    slack_client.api_call(
        "chat.postMessage",
        channel='general',
        text=response
    )
    slack_client.api_call(
        "chat.postMessage",
        channel='assignment1',
        text=response
    )
    threading.Timer(86400, timelypost).start()

if __name__ == "__main__":

    timelypost()

    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
