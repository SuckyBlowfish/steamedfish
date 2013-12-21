import sys
from steamedfish.steam3 import SteamClient, SteamFriends
from steamedfish.steam3.steam_events import SendFriendMessage, SetPersonaState
from steamedfish.steam_base import EChatEntryType, EMsg, EPersonaState
from steamedfish import Util
from circuits import Debugger, Component
from circuits.core import handler
from chatterbotapi import ChatterBotFactory, ChatterBotType

from steam_logger import SteamLogger

class SteamEcho(Component):
    channel = 'steam'

    def __init__(self, username, password):
        super(SteamEcho, self).__init__()
        self.username = username
        self.password = password

    def started(self, *args):
        self.client = SteamClient().register(self)
        self.steam_friends = SteamFriends().register(self)
        SteamLogger().register(self)
        self.client.connect()
        self.friend_bots = {}
        self.factory = ChatterBotFactory()

    @handler('friend_message')
    def _friend_message(self, steamid, chat_entry_type, message):
        if chat_entry_type == EChatEntryType.ChatMsg:
            print('[Incoming Friend Message] ' + message)
            self.stimulate_chatter_bot(steamid, message)

    def stimulate_chatter_bot(self, steamid, message):
        if steamid not in self.friend_bots:
            bot = self.factory.create(ChatterBotType.CLEVERBOT)
            bot_session = bot.create_session()
            self.friend_bots[steamid] = bot_session

        bot_session = self.friend_bots[steamid]
        response = bot_session.think(message)
        self.fire(SendFriendMessage(steamid, EChatEntryType.ChatMsg, response))

    @handler('send_friend_message')
    def _send_friend_message(self, steamid, chat_entry_type, message):
        if chat_entry_type == EChatEntryType.ChatMsg:
            print('[Outgoing Friend Message] ' + message)

    @handler('logged_on')
    def _handle_logged_on(self, steamid):
        self.fire(SetPersonaState(EPersonaState.Online))

    @handler('connected')
    def _handle_connected(self):
        self.client.login(self.username, self.password)

if __name__ == '__main__':
    if not len(sys.argv) >= 3:
        print('Usage: ' + sys.argv[0] + ' username password')
        sys.exit()
    username = sys.argv[1]
    password = sys.argv[2]
    SteamEcho(username, password).run()
