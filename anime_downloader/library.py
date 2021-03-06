# Copyright (C) 2020-2021 k4leg <python.bogdan@gmail.com>
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

"""Core classes and functions.

This module exports the following classes:
    Anime  Instance of this class contains the `title`, `url` and
           `playlist` attributes.
    Config  Represent a config object that parse a JSON file.
    Playlist  Represent a playlist object.
    SearchQuery  Represent a search query object.

This module exports the following functions:
    get_db  Return the DB.
    push_db  Push DB.
    get_page  Return a page.
    get_updated_anime_from_db  Return a list of updated anime.
    print_db  Print the DB.
    update_and_save_all_db  Update all playlists in the DB.
"""

__all__ = [
    'Anime',
    'Config',
    'DEFAULT_PATH_TO_DB',
    'Playlist',
    'SearchQuery',
    'get_db',
    'get_page',
    'get_updated_anime_from_db',
    'print_db',
    'update_and_save_all_db',
]

import json
import os
import pickle
from abc import ABCMeta, abstractmethod
from functools import total_ordering
from typing import Iterable, NoReturn, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from rich.progress import Progress

from anime_downloader.downloader import Downloader
from anime_downloader.exceptions import *

DEFAULT_PATH_TO_DB = os.path.expanduser('~/.config/anime-downloader/db')


class Anime(metaclass=ABCMeta):
    """
    Instance of this class contains the `title`, `url` and `playlist`
    attributes.
    """

    def __init__(self, url: str, title: Optional[str] = None) -> None:
        self.url = url
        self.title = self._get_title() if title is None else title
        self.update_playlist()

    @abstractmethod
    def update_playlist(self) -> None:
        """Update the `self.playlist`."""

    @abstractmethod
    def _get_title(self) -> str:
        """Return the title."""

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}('{self.url}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, Anime):
            return ((self.url, self.title, self.playlist)
                    == (other.url, other.title, other.playlist))
        return NotImplemented

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Config:
    """Represent a config object that parse a JSON file.

    The attributes of instance of this class represent the JSON file
    itself.
    """

    def __init__(self, path_to_config: str, **kwargs) -> None:
        self._path = os.path.abspath(path_to_config)
        if os.path.exists(self._path):
            self._load_config()
            if kwargs:
                self._set_dict_as_attrs(kwargs)
        else:
            try:
                self._dump_config(**kwargs)
            except TypeError:
                raise NotEnoughArgumentsToInitializeError from None
            else:
                self._load_config()

    def save(self) -> None:
        """Save config using instance attributes."""
        cfg = self.__dict__.copy()
        del cfg['_path']
        self._dump_config(**cfg)

    def _dump_config(self, **kwargs) -> None:
        """Save the config by accepting arguments.

        Raises `TypeError` if an empty kwargs is passed.
        """
        if not kwargs:
            raise TypeError("kwargs argument must not be empty")

        with open(self._path, 'w') as f:
            json.dump(kwargs, f)

    def _load_config(self) -> None:
        """Recreate the config as a Python object by scanning a JSON file."""
        with open(self._path) as f:
            cfg = json.load(f)
        self._set_dict_as_attrs(cfg)

    def _set_dict_as_attrs(self, attrs: dict, /) -> None:
        """
        Concatenate `self.__dict__` and `attrs`, replacing objects from
        `attrs`if any.
        """
        for key, value in attrs.items():
            setattr(self, key, value)


@total_ordering
class Playlist:
    """Represent a playlist object.

    Instance of this class contain the `playlist` attribute that
    contains a tuple of urls.
    """

    def __init__(self, urls: Iterable[str], /) -> None:
        self.playlist = tuple(urls)

    def download(
        self,
        episode: Optional[int] = None,
        path_to_downloads: str = '~/Downloads',
    ) -> None:
        """Download the episode."""
        try:
            url = self[episode]
        except IndexError:
            raise NoEpisodeFoundError from None
        Downloader([url], path_to_downloads)

    def download_episodes(
        self,
        episode_start: Optional[int] = None,
        episode_stop: Optional[int] = None,
        path_to_downloads: str = '~/Downloads',
    ) -> None:
        """Download the episodes."""
        try:
            episodes = self[episode_start:episode_stop]
        except IndexError:
            raise NoEpisodeFoundError from None
        Downloader(episodes, path_to_downloads)

    def index(
        self,
        value: Union[str, Tuple[str, ...]],
        start: int = 1,
        stop: int = 9223372036854775807,
    ) -> int:
        """Return first index of value.

        Raises `ValueError` if the value is not present.
        """
        return self.playlist.index(value, start - 1, stop) + 1

    def __lt__(self, other) -> bool:
        if isinstance(other, Playlist):
            return self.playlist < other.playlist
        return NotImplemented

    def __eq__(self, other) -> bool:
        if isinstance(other, Playlist):
            return self.playlist == other.playlist
        return NotImplemented

    def __len__(self) -> int:
        return len(self.playlist)

    def __getitem__(
        self, key: Union[int, slice, None]
    ) -> Union[str, Tuple[str, ...]]:
        """
        The index starts at 1 and ends at `len(self)` inclusive.  If
        `None` was passed then the last element is returned.  When
        slicing, you can only specify indices that exist (that is, from
        1 to `len(self)`) or `None`.

        Raises a `TypeError` on an unsupported type.
        """
        range_ = {*range(len(self.playlist)), None}

        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            if start is not None:
                start -= 1
            if start not in range_ or stop not in range_:
                raise IndexError
            if start is not None and stop is not None:
                if start > stop:
                    raise IndexError
            return self.playlist[start:stop:step]
        elif isinstance(key, int):
            key -= 1
            if key not in range_:
                raise IndexError
            return self.playlist[key]
        elif key is None:
            return self.playlist[-1]
        raise TypeError


class SearchQuery:
    """Represent a search query object.

    Instance of this class contain a `anime_list` attribute.  This type
    object is immutable.
    """

    def __init__(
        self, search_query_text: str, /, *, format: bool = True
    ) -> None:
        object.__setattr__(self, '_search_query_text', search_query_text)
        object.__setattr__(self, '_format', format)
        object.__setattr__(
            self, 'anime_list', self._get_search_query_results()
        )

    @abstractmethod
    def _get_search_query_results(self) -> Tuple[Anime, ...]:
        """Return a tuple of anime.

        Raises `SearchQueryDidNotReturnAnyResultsError` if search query
        return an empty anime list.
        """

    def __bool__(self) -> bool:
        return bool(self.anime_list)

    def __setattr__(self, key, value) -> NoReturn:
        class_name = self.__class__.__name__
        if key in dir(self):
            raise AttributeError(
                f"'{class_name}' object attribute '{key}' is read-only"
            )
        raise AttributeError(f"'{class_name}' object has no attribute '{key}'")

    def __len__(self) -> int:
        return len(self.anime_list)

    def __getitem__(
        self, key: Union[int, slice]
    ) -> Union[Anime, Tuple[Anime, ...]]:
        return self.anime_list[key]

    def __setitem__(self, key, value) -> NoReturn:
        class_name = self.__class__.__name__
        raise TypeError(
            f"'{class_name}' object does not support item assignment"
        )

    def __iter__(self) -> Iterable[Anime]:
        return iter(self.anime_list)


def get_db(path_to_db: str) -> list:
    """Return the DB."""
    with open(path_to_db, 'rb') as f:
        db = pickle.load(f)
    return db


def push_db(db: list, path_to_db: str) -> None:
    """Push DB."""
    with open(path_to_db, 'wb') as f:
        pickle.dump(db, f)


def get_page(url: str, **kwargs) -> BeautifulSoup:
    """Return a page."""
    response = requests.get(url, **kwargs)
    return BeautifulSoup(response.content, 'html.parser')


def get_updated_anime_from_db(path_to_db: str) -> list:
    """Return a list of updated anime.

    Raises `AnimeListHasNotBeenUpdatedError` if the list is empty.
    """
    db = get_db(path_to_db)
    res = [anime for anime in db if anime.is_modified_after_update]
    if not res:
        raise AnimeListHasNotBeenUpdatedError
    return res


def print_db(path_to_db: str) -> None:
    """
    Print the DB in the following format:
    n. title (url)
    """
    try:
        db = get_db(path_to_db)
    except FileNotFoundError:
        print("No DB created.")
    else:
        if db:
            for n, anime in enumerate(db, 1):
                title, url = anime.title, anime.url
                print(f"{n}. {title} ({url})")
        else:
            print("There is nothing in the DB.")


def update_and_save_all_db(
    path_to_db: str,
    *,
    progress_bar: bool = False,
    progress_bar_text: Optional[str] = None,
) -> None:
    """Update all playlists in the DB."""
    db = get_db(path_to_db)

    updated_db = []
    if progress_bar:
        with Progress(transient=True) as progress:
            if progress_bar and progress_bar_text is None:
                progress_bar_text = "DB update"
            task = progress.add_task(progress_bar_text, total=len(db))
            for anime in db:
                anime.update_playlist()
                if anime not in updated_db:
                    updated_db.append(anime)
                progress.update(task, advance=1)
    else:
        for anime in db:
            anime.update_playlist()
            if anime not in updated_db:
                updated_db.append(anime)

    push_db(updated_db, path_to_db)


def remove_from_db(obj, path_to_db: str) -> None:
    """Remove an object from the DB.

    Raises `ObjectNotFoundInDBError` if instance isn't in the DB.
    """
    db = get_db(path_to_db)

    try:
        db.remove(obj)
    except ValueError:
        raise ObjectNotFoundInDBError(obj) from None

    push_db(db, path_to_db)
