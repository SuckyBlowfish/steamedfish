from steamkit.steam_base import EMsg
from steamkit import Util

from circuits import Component

get_msg = Util.get_msg

class SteamLogger(Component):

    channel = 'steam'
    
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'

    def __init__(self, ignorelist=[EMsg.ClientHeartBeat], *args, **kwargs):
        super(SteamLogger, self).__init__(*args, **kwargs)
        self.ignorelist = ignorelist

    def message(self, emsg_real, msg):
        emsg = get_msg(emsg_real)
        if emsg in self.ignorelist:
            return
        out = self.OKBLUE
        out += '[msg < ] '
        out += str(emsg)
        out += ': '
        out += str(Util.lookup_enum(EMsg, emsg))
        out += self.END
        print(out)

    def send_message(self, msg):
        emsg_real = msg.header.emsg
        emsg = get_msg(emsg_real)
        if emsg in self.ignorelist:
            return
        out = self.OKGREEN
        out += '[msg > ] '
        out += str(emsg)
        out += ': '
        out += str(Util.lookup_enum(EMsg, emsg))
        out += self.END
        print(out)
