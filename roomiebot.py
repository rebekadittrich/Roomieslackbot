import os
import time
import re
import requests
import Levenshtein
from slackclient import SlackClient

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
FROM_COMMAND = ""
TO_COMMAND = "to"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response_message = "I didn't quite get that. Can you make your message simpler?"
    try:
        if command.startswith(FROM_COMMAND):
            number = len(command.split())
            if number >= 2:
                rooms = [
                    'Spline', 'Cat\'s cradle', 'Hypercube', 'Fractal', 'Icosidodecahedron', 'Eames', 'Regina', 'Lovelace',
                    'Turing', 'Erdos', 'ContentArranger', 'EagleTransition', 'UserCell', 'AbstractElement',
                    'Please', 'Workshop', 'Geographer', 'Asteroid b-612', 'Elephant', 'Lamplighter', 'Rose', 'Baobab',
                    'Cinema', 'Totoro', 'Sangaku', 'Donkey Kong', 'Fuji', 'Stretch', 'Bob'
                ]
                rooms_without_bob = [room for room in rooms if room != 'Bob']

                first_word = ""
                second_word = ""
                first_room = ""
                second_room = ""
                from_room = ""
                to_room = ""
                command1 = str(command).lower()
                command = str(command).lower()
                command = re.sub("[^\w]", " ", command).split()

                bob_found = 'bob' in command
                min_lemming = 1000000
                for word in command:
                    for room in rooms_without_bob if bob_found else rooms:
                        if Levenshtein.distance(word, room) < min_lemming:
                            min_lemming = Levenshtein.distance(word, room)
                            first_word, first_room = word, room

                indexfrom = command1.index(first_word)
                rooms.remove(first_room)
                command.remove(first_word)

                if not bob_found:
                    min_lemming2 = 1000000
                    for word in command:
                        for room in rooms:
                            if Levenshtein.distance(word, room) < min_lemming2:
                                min_lemming2 = Levenshtein.distance(word, room)
                                second_word, second_room = word, room
                else:
                    second_word, second_room = 'bob', 'Bob'

                indexto = command1.index(second_word)

                if indexfrom < indexto:
                    from_room = first_room
                    to_room = second_room
                elif indexfrom > indexto:
                    from_room = second_room
                    to_room = first_room

                response = requests.get("https://roomieapp.herokuapp.com/direction/?searchFrom=" + from_room + "&searchTo=" + to_room)

                desc = response.json()
                pathdesc = desc["path"]

                response_message = "The route from " + from_room + " to " + to_room + "\n"

                for path in pathdesc:
                    response_message += path
                    response_message += '\n'
                response_message += ("For more information please visit us at <https://roomieapp.herokuapp.com/?searchFrom=" + from_room + "&searchTo=" + to_room + ">")
            else:
                response_message = "Where do you stand and where do you want to go?"
    except Exception as e:
        print e
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response_message, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output:
                if output['channel'].startswith('D') and output.get('bot_id') is None:
                    return output['text'], output['channel']
                if AT_BOT in output['text']:
                    # return text after the @ mention, whitespace removed
                    return output['text'].split(AT_BOT)[1].strip().lower(), \
                           output['channel']
    return None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("Roomie connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
