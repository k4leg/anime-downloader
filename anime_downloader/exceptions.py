"""
This module exports the following exceptions:
    AnimeException
        SearchQueryLenError
        NoEpisodeFoundError
        SearchQueryDidNotReturnAnyResultsError
        UserEnteredIncorrectDataError
        NotExistsEpisodeError
        NotALinkPassedError
        ObjectNotFoundInDBError
        NoUpdatedReleasesError
        NoDBError
        UndefinedBehaviorError
        AnotherInstanceAlreadyRunError
        NotEnoughArgumentsToInitializeError
"""


class AnimeException(Exception):
    error_message = ""

    def __str__(self):
        if self.args and not self.error_message:
            return ' '.join(self.args)
        elif self.args:
            return self.error_message + f" ({' '.join(self.args)})"

        return self.error_message


class SearchQueryLenError(AnimeException):
    error_message = "request length must be greater than 3"


class NoEpisodeFoundError(AnimeException):
    pass


class SearchQueryDidNotReturnAnyResultsError(AnimeException):
    pass


class UserEnteredIncorrectDataError(AnimeException):
    pass


class NotExistsEpisodeError(AnimeException):
    pass


class NotALinkPassedError(AnimeException):
    pass


class ObjectNotFoundInDBError(AnimeException):
    pass


class NoUpdatedReleasesError(AnimeException):
    pass


class NoDBError(AnimeException):
    pass


class UndefinedBehaviorError(AnimeException):
    pass


class AnotherInstanceAlreadyRunError(AnimeException):
    pass


class NotEnoughArgumentsToInitializeError(AnimeException):
    pass
