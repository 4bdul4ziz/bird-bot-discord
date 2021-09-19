from enum import Enum


class Error(Exception, Enum):
    MissingPermissions = "The bot is missing the needed permissions"
    NotAllowed = "You are not allowed to execute this action, either because \
        you are missing the needed permissions or because your roles are not \
        high enough"
    MissingSettings = "The required settings for this operation are missing"
    NotGiveable = "This role has not been set as giveable and thus can not be \
        granted or taken away by this bot"
    AlreadyDone = "This action has already been completed, or the result of \
        it already exists and can not be repeated"
    MissingArgument = "One or more required arguments are missing"
