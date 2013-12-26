from circuits import Event

class Connected(Event):
    """
    Fired when we successfully connect to steam servers and complete the encryption request
    """

class ProtocolMessage(Event):
    """
    Used for messages client-server messages
    """

class SendProtocolMessage(Event):
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

