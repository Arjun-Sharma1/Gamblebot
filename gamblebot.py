import sys
import time
import random
from slackclient import SlackClient
from gamblegame import GambleGame

class GambleBot:

    def __init__(self, token, id):
        API_TOKEN = token
        BOT_ID = id
        self.AT_BOT = "<@" + BOT_ID + ">"
        self.game = GambleGame()
        self.slack_client = SlackClient(API_TOKEN)

    def post(self, response, channel):
        self.slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

    def get_user_input(self, player):
        while(True):
            username, command, channel = self.parse_slack_output(self.slack_client.rtm_read())
            if(command and channel):
                if username != None and username == player and command.split()[1] == "roll":
                    return

    def get_bet_amount(self):
        betted_users = []
        timeout = time.time() + 30   # 5 minutes from now
        while True:
            if len(betted_users) == len(self.game.current_players) or time.time() > timeout:
                break
            username, command, channel = self.parse_slack_output(self.slack_client.rtm_read())
            if(command and channel):
                command_split = command.split()
                if username != None and len(command_split) == 3 and command_split[1] == "bet":
                    if (username in betted_users):
                        response = username + " has already placed a bet"
                    else:
                        try:
                            bet = self.game.players[username].bet(int(command_split[2]))
                            if type(bet) is str:
                                response = username + " you do not have enough money to place that bet"
                            else:
                                self.game.current_players[username] = bet
                                betted_users.append(username)
                                response = username + " placed a bet of " + str(command_split[2])
                        except:
                            response = "bet amount is not correct"

                    self.post(response, channel)
        self.post("Betting is now complete. Users who did not bet will be removed from current game", channel)
        time.sleep(1)
        '''for user in self.game.current_players.keys():
            if user not in betted_users:
                self.game.current_players.pop(user)'''

        return sum(bet for bet in self.game.current_players.values()) #return sum of all bets

    def handle_command(self, username, command, channel):
        print(command)
        response = ""
        if len(command.split()) > 1:
            gamble_command = command.split()[1]
            if gamble_command == "join":
                response = self.game.add_player(username)

            elif gamble_command == "start":
                response = self.game.start()
                if response == "":
                    self.post("30 seconds to bet, type 'bet <amount> to place bet", channel)
                    total_pot = self.get_bet_amount()
                    for player_name in self.game.players.keys():
                        response = player_name + "'s turn to roll"
                        self.post(response, channel)
                        self.get_user_input(player_name)

                        random_int = self.game.players[player_name].roll()
                        self.game.update_winner(player_name, random_int)
                        response = "You rolled " + str(random_int)
                        self.post(response, channel)
                        time.sleep(1)
                    response = "Winner of this round is " + self.game.winning_player_name
                    self.game.end(total_pot)

            elif gamble_command == "list":
                response = self.game.list_players()

            elif gamble_command == "score":
                response = self.game.list_score()

            elif gamble_command == "help":
                response = "join - join existing game\n" \
                           "start - start game\n" \
                           "list - list current players\n" \
                           "score - list all stored players and their score\n"

            elif gamble_command == "winnings":
                response = self.game.list_winning(username)
        else:
            response="Use 'join' to join the game"

        self.post(response, channel)


    def parse_slack_output(self, slack_rtm_output):
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and self.AT_BOT in output['text']:
                    username = self.slack_client.api_call("users.info", user=output['user'])['user']['name']
                    return username, output['text'].strip().lower(), output['channel']
        return None, None, None

    def listen(self):
        READ_WEBSOCKET_DELAY = 1
        if self.slack_client.rtm_connect():
            print("Bot connected and running!")
            while True:
                username, command, channel = self.parse_slack_output(self.slack_client.rtm_read())
                if command and channel:
                    self.handle_command(username, command, channel)
        else:
            print("Connection failed.")


if __name__ == "__main__":
    token = sys.argv[1]
    id = sys.argv[2]
    bot = GambleBot(token, id)
    bot.listen()


