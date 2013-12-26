from circuits import Event

# TODO: change to ProtocolMessage
class Message(Event):
    """
    Used for messages client-server messages
    """

# TODO: change to SendProtocolMessage
class SendMessage(Event):
    """
    Used for sending a protobuf message to steam servers
    """

class LoggedOn(Event):
    """
    When a client has successfully logged on
    """

class FriendRequest(Event):
    pass

class FriendMessage(Event):
    pass

class SendFriendMessage(Event):
    pass

class ClientChangeStatus(Event):
    pass

class SetPersonaState(Event):
    pass

