import binascii
import struct
import StringIO
import zipfile
from circuits.net.sockets import Write
from circuits.core import Timer, handler
from circuits import Component, Event

from steamedrice.crypto import CryptoUtil
from steamedrice.protobuf import steammessages_clientserver_pb2, steammessages_base_pb2
from steamedrice.steam3.steam_events import ProtocolMessage, SendProtocolMessage, LoggedOn, Connected
from steamedrice.steam3 import msg_base
from steamedrice.steam_base import EMsg, EUniverse, EResult
from steamedrice import Util, SteamID

class ProtocolError(Exception):
    """
    Raise when an error has occurred in the Steam protocol
    """

class Heartbeat(Event):
    pass

class NetEncryption():
    def __init__(self, key):
        self.key = key

    def process_incoming(self, data):
        return CryptoUtil.symmetric_decrypt(data, self.key)

    def process_outgoing(self, data):
        return CryptoUtil.symmetric_encrypt(data, self.key)

class SteamProtocol(Component):
    """Handles the parsing and event generation from all steam messages"""

    channel = '*'

    def __init__(self):
        super(SteamProtocol, self).__init__()
        self.read_buffer = b''
        self.netfilter = None

        self.session_key = None
        self.session_id = None
        self.steamid = None
        
    def dispatch_message(self, msg):
        emsg_real, = struct.unpack_from('<I', msg)
        emsg = Util.get_msg(emsg_real)

        self.fire(ProtocolMessage(emsg_real, msg), 'steam')

        if emsg == EMsg.ChannelEncryptRequest:
            self.channel_encrypt_request(msg)
        elif emsg == EMsg.ChannelEncryptResult:
            self.channel_encrypt_result(msg)
        elif emsg == EMsg.ClientLogOnResponse:
            self.client_logon_response(msg)
        elif emsg == EMsg.Multi:
            self.split_multi_message(msg)

    def channel_encrypt_request(self, msg):
        message = msg_base.Message(msg_base.MsgHdr, msg_base.ChannelEncryptRequest)
        message.parse(msg)

        if message.body.protocol_version != 1:
            raise ProtocolError('Unexpected channel encryption protocol')

        if message.body.universe != EUniverse.Public:
            raise ProtocolError('Unexpected universe in encryption method')

        self.session_key = CryptoUtil.create_session_key()
        crypted_key = CryptoUtil.rsa_encrypt(self.session_key)
        key_crc = binascii.crc32(crypted_key) & 0xFFFFFFFF

        response = msg_base.Message(msg_base.MsgHdr, msg_base.ChannelEncryptResponse, EMsg.ChannelEncryptResponse)
        response.body.protocol_version = 1
        response.body.key_size = len(crypted_key)
        response.payload = crypted_key + struct.pack('II', key_crc, 0)

        self.fire(SendProtocolMessage(response), 'steam')

    def channel_encrypt_result(self,msg):
        message = msg_base.Message(msg_base.MsgHdr, msg_base.ChannelEncryptResult)
        message.parse(msg)

        if message.body.result != EResult.OK:
            raise ProtocolError('Unable to negotiate channel encryption')
        self.netfilter = NetEncryption(self.session_key)
        self.fire(Connected(), 'steam')
    
    def client_logon_response(self, msg):
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientLogonResponse)
        message.parse(msg)

        if message.body.eresult == EResult.OK:
            self.session_id = message.proto_header.client_sessionid
            self.steamid = SteamID(message.proto_header.steamid)

            delay = message.body.out_of_game_heartbeat_seconds
            Timer(delay, Heartbeat(), persist=True).register(self)

            self.fire(LoggedOn(self.steamid), 'steam')

    def split_multi_message(self, msg):
        message = msg_base.ProtobufMessage(steammessages_base_pb2.CMsgMulti)
        message.parse(msg)

        payload = message.body.message_body

        if message.body.size_unzipped > 0:
            zip_buffer = StringIO.StringIO(message.body.message_body)
            with zipfile.ZipFile(zip_buffer, 'r') as zip:
                payload = zip.read('z')

        i = 0
        while i < len(payload):
            sub_size, = struct.unpack_from ('<I', payload, i)
            self.dispatch_message(payload[i+4:i+4+sub_size])
            i += sub_size + 4

    @handler('heartbeat')
    def _heartbeat(self):
        message = msg_base.ProtobufMessage(steammessages_clientserver_pb2.CMsgClientHeartBeat, EMsg.ClientHeartBeat)
        self.fire(SendProtocolMessage(message), 'steam')

    @handler('send_protocol_message', 'steam')
    def send_protocol_message(self, msg):
        if self.session_id:
            msg.header.session_id = self.session_id
        if self.steamid:
            msg.header.steamid = self.steamid.steamid

        msg = msg.serialize()
        if self.netfilter:
            msg = self.netfilter.process_outgoing(msg)

        msg = struct.pack('I4s', len(msg), b'VT01') + msg

        self.fire(Write(msg), 'steamcon')

    @handler('read', 'steamcon')
    def read(self, data):
        self.read_buffer += data

        while len(self.read_buffer) >= 8:
            length, magic = struct.unpack_from('<I4s', self.read_buffer)

            if magic != b'VT01':
                raise ProtocolError('Invalid packet magic')
            if len(self.read_buffer) < length + 8:
                break

            buffer = self.read_buffer[8:length+8]
            if self.netfilter:
                buffer = self.netfilter.process_incoming(buffer)

            self.dispatch_message(buffer)
            self.read_buffer = self.read_buffer[length+8:]
