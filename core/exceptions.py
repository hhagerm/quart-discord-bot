class DoorBellException(Exception):
    pass

class DeviceUnauthorizedError(DoorBellException):
    pass

class DatabaseError(DoorBellException):
    pass

class ImageProcessingError(DoorBellException):
    pass

class NotificationServiceError(DoorBellException):
    pass

class InvalidImageFormatError(DoorBellException):
    pass


class DiscordBotException(Exception):
    pass

class ChannelNotFoundError(DiscordBotException):
    pass