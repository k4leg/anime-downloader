# Copyright (C) 2020 k4leg <python.bogdan@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
        LinkHasNoIDError
"""


class AnimeException(Exception):
    error_message = ""

    def __str__(self):
        return f"{self.error_message} ({', '.join(self.args)})"


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


class LinkHasNoIDError(AnimeException):
    pass
