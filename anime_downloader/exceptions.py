"""
This module exports the following exceptions:
    AnimevostParserException
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


class AnimevostParserException(Exception):
    error_message = ""

    def __str__(self):
        if self.args and not self.error_message:
            return ' '.join(self.args)
        elif self.args:
            return self.error_message + f" ({' '.join(self.args)})"

        return self.error_message


class SearchQueryLenError(AnimevostParserException):
    error_message = "request length must be greater than 3"


class NoEpisodeFoundError(AnimevostParserException):
    pass


class SearchQueryDidNotReturnAnyResultsError(AnimevostParserException):
    pass


class UserEnteredIncorrectDataError(AnimevostParserException):
    pass


class NotExistsEpisodeError(AnimevostParserException):
    pass


class NotALinkPassedError(AnimevostParserException):
    pass


class ObjectNotFoundInDBError(AnimevostParserException):
    pass


class NoUpdatedReleasesError(AnimevostParserException):
    pass


class NoDBError(AnimevostParserException):
    pass


class UndefinedBehaviorError(AnimevostParserException):
    pass


class AnotherInstanceAlreadyRunError(AnimevostParserException):
    pass


class NotEnoughArgumentsToInitializeError(AnimevostParserException):
    pass
