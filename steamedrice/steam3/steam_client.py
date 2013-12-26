from circuits import Component
from circuits.net.sockets import TCPClient, Connect, Disconnect
from circuits.core import handler

from steamedrice import SteamID, Util
from steamedrice.steam3 import msg_base
from steamedrice.steam3.steam_friends import SteamFriends
from steamedrice.steam3.steam_protocol import SteamProtocol
from steamedrice.steam3.steam_events import SendProtocolMessage, SetPersonaState
from steamedrice.protobuf import steammessages_clientserver_pb2
from steamedrice.steam_base import EMsg, EResult, EUniverse, EAccountType, EPersonaState

base_server_list = [('72.165.61.174', 27017), ('72.165.61.174', 27018)]


class SteamClient(Component):
    channel = 'steam'

    def __init__(self):
        super(SteamClient, self).__init__()

        self.username = None
        self.steam2_ticket = None
        self.session_token = None
        self.server_list = dict()
        self.account_type = None

        self.steam_friends = SteamFriends().register(self)

        SteamProtocol().register(self)

        self._transport = TCPClient(channel='steamcon').register(self)

    def ready(self, *args):
        self.connect()

    def connect(self):
        addr = base_server_list.pop(0)
        if not self._transport.connected:
            self.fire(Connect(*addr), 'steamcon')

    def disconnect(self):
        if self.steamid:
            self.logout(self)
        self.fire(Disconnect(), 'steamcon')

    def login(self, username=None, password=None, login_key=None, auth_code=None, steamid=0):
        self.username = username
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientLogon, EMsg.ClientLogon)
        message.proto_header.client_sessionid = 0
        if steamid > 0:
            message.proto_header.steamid = steamid
        else:
            message.proto_header.steamid = SteamID.make_from(0, 0, EUniverse.Public, EAccountType.Individual).steamid
        message.body.protocol_version = 65575
        message.body.client_package_version = 1771
        message.body.client_os_type = 10
        message.body.client_language = "english"
        message.body.machine_id = "OK"

        message.body.account_name = username
        message.body.password = password

        if login_key:
            message.body.login_key = login_key
        if auth_code:
            message.body.auth_code = auth_code
        
        # TODO: create the actual file
        sentryfile = self.get_sentry_file(username)
        if sentryfile:
            message.body.sha_sentryfile = Util.sha1_hash(sentryfile)
            message.body.eresult_sentryfile = EResult.OK
        else:
            message.body.eresult_sentryfile = EResult.FileNotFound
        
        message.body.obfustucated_private_ip = 1111

        self.fire(SendProtocolMessage(message))

    def get_sentry_file(self, username):
        return '.steam.sentry'

    @handler('logged_on')
    def _logged_on(self, steamid):
        self.steamid = steamid
        self.fire(SetPersonaState(EPersonaState.Online))
