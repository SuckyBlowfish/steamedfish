from steamedrice.protobuf import steammessages_clientserver_pb2
from steamedrice.steamid import SteamID
from steamedrice.steam3 import msg_base
from steamedrice.steam_base import EMsg, EFriendRelationship, EPersonaState
from steamedrice.util import Util
from circuits import Component
from circuits.core import handler
from steam_events import FriendMessage, SendProtocolMessage, FriendRequest

get_msg = Util.get_msg

class User():
    def __init__(self, steamid=None, persona_state=0, persona_name=None, friend_relationship=None,
            game_played_id=None, game_played_name=None, persona_state_flags = 0):
        self.steamid = steamid
        self.persona_state = persona_state
        self.person_state_flags = persona_state_flags
        self.persona_name = persona_name
        self.friend_relationship = friend_relationship
        self.game_played_id = game_played_id
        self.game_played_name = game_played_name

class SteamFriends(Component):

    channel = 'steam'

    def __init__(self):
        super(SteamFriends, self).__init__()
        
        self.friends_list = {}
        self.local_user = User()

    @handler('protocol_message')
    def handle_protocol_message(self, emsg, msg):
        if get_msg(emsg) == EMsg.ClientFriendMsgIncoming:
            self._handle_client_friend_msg_incoming(msg)
        elif get_msg(emsg) == EMsg.ClientFriendsList:
            self._handle_client_friends_list(msg)
        elif get_msg(emsg) == EMsg.ClientAccountInfo:
            self._handle_client_account_info(msg)

    @handler('logged_on')
    def _logged_on(self, steamid):
        self.local_user.steamid = steamid

    def set_persona_state(self, persona_state):
        self.local_user.persona_state = persona_state
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientChangeStatus,
                EMsg.ClientChangeStatus)
        message.body.persona_state = self.local_user.persona_state
        self.fire(SendProtocolMessage(message), 'steam')

    def set_player_name(self, player_name):
        self.local_user.player_name = player_name
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientChangeStatus,
                EMsg.ClientChangeStatus)
        message.body.player_name = self.local_user.player_name
        message.body.persona_state = self.local_user.persona_state or EPersonaState.Offline
        self.fire(SendProtocolMessage(message), 'steam')

    def send_friend_message(self, steamid, chat_entry_type, msg):
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientFriendMsg,
                EMsg.ClientFriendMsg)
        message.body.steamid = steamid
        message.body.chat_entry_type = chat_entry_type
        message.body.message = msg
        self.fire(SendProtocolMessage(message), 'steam')

    def _handle_client_friend_msg_incoming(self, msg):
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientFriendMsgIncoming,
                EMsg.ClientFriendMsgIncoming)
        message.parse(msg)
        self.fire(FriendMessage(message.body.steamid_from, message.body.chat_entry_type, message.body.message))

    def _handle_client_friends_list(self, msg):
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientFriendsList,
                EMsg.ClientFriendsList)
        message.parse(msg)
        if not message.body.bincremental:
            self.friends_list = {}
        # TODO: handle more friend information
        for friend in message.body.friends:
            self.friends_list[friend.ulfriendid] = User(steamid=friend.ulfriendid)
            if friend.efriendrelationship == EFriendRelationship.RequestInitiator:
                self.fire(FriendRequest(friend.ulfriendid))

    def _handle_client_account_info(self, msg):
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientAccountInfo,
                EMsg.ClientAccountInfo)
        message.parse(msg)
        self.local_user.player_name = message.body.persona_name
