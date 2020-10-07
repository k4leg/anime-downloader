"""Core classes and functions.

This module exports the following classes:
    Playlist  Represent a playlist object.
    Config    Represent a config object that parse a JSON file.

This module exports the following functions:
    get_db                        Return the DB.
    print_db                      Print the DB.
    get_updated_releases_from_db  Update all playlists in the DB.
    get_page                      Return a page.
    download                      Downloads a file.
"""

import json
import os
import pickle
from abc import ABCMeta, abstractmethod
from functools import total_ordering
from typing import List, Optional, Union

import requests
from bs4 import BeautifulSoup
from rich.progress import Progress

from anime_downloader.exceptions import *

URL = str


@total_ordering
class Playlist:
    """Represent a playlist object.

    Instance of this class contain the playlist attribute that contains a list of
    links.
    """

    def __init__(self, links_to_episodes: List[URL], *, copy: bool = True) -> None:
        self.playlist = links_to_episodes.copy() if copy else links_to_episodes

    def index(self, value: URL, start: int = 1, stop: int = 9223372036854775807) -> int:
        """Return first index of value.

        Raises ValueError if the value is not present.
        """
        return self.playlist.index(value, start - 1, stop) + 1

    def copy(self) -> 'Playlist':
        """Return a shallow copy of the Playlist."""
        return Playlist(self.playlist)

    def __lt__(self, other: 'Playlist') -> bool:
        return self.playlist < other.playlist

    def __eq__(self, other: 'Playlist') -> bool:
        return self.playlist == other.playlist
    
    def __len__(self) -> int:
        return len(self.playlist)

    def __getitem__(self, key: Union[int, slice]) -> Union[URL, List[URL]]:
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


class Config:
    """Represent a config object that parse a JSON file.

    The attributes of instance of this class represent the JSON file itself.
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

        Raises TypeError if an empty kwargs is passed.
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

    def _set_dict_as_attrs(self, d: dict, /) -> None:  # FIXME: rename 'd'
        """Concatenate self.__dict__ and d, replacing objects from d if any."""
        for key, value in d.items():
            setattr(self, key, value)


class Release(metaclass=ABCMeta):
    """
    Instance of this class contain the attributes of the link to the release and
    the title of the release.  The release name can be taken from the link by
    implementing the _get_title method and if the release name has been passed
    then unnecessary actions for calling the _get_title method are not done.
    """

    def __init__(self, link: URL, title: Optional[str] = None) -> None:
        self.link = link
        self.update_title(title)

    def update_title(self, title: Optional[str] = None) -> None:
        """Update the release name."""
        self.title = self._get_title(self.link) if title is None else title

    @staticmethod
    @abstractmethod
    def _get_title(link: str) -> str:
        """Return the name of the release."""

    def __str__(self) -> str:
        clsname = self.__class__.__name__
        return f"{clsname}('{self.title}', '{self.link}')"


def get_db(path_to_db: str) -> list:
    """Return the DB."""
    with open(path_to_db, 'rb') as f:
        db = pickle.load(f)
    return db


def print_db(path_to_db: str) -> None:
    """
    Print the DB in the following format:
    n. title (link)
    """
    try:
        db = get_db(path_to_db)
    except FileNotFoundError:
        print("No DB created.")
    else:
        if db:
            for n, animevost_instance in enumerate(db, 1):
                release = animevost_instance.release
                title = release.title
                link = release.link
                print(f"{n}. {title} ({link})")
        else:
            print("There is nothing in the DB.")


def update_and_save_all_db(path_to_db: str) -> None:
    """Update all playlists in the DB."""
    db = get_db(path_to_db)
    for animevost_instance in db:
        animevost_instance.update()
        animevost_instance.save_to_db(path_to_db)


def get_updated_anime_from_db(path_to_db: str) -> list:
    """Return a list of updated releases.

    Raises NoUpdatedReleasesError if the list is empty.
    """
    db = get_db(path_to_db)
    res = [animevost for animevost in db if animevost.playlist.is_modified_after_update]
    if not res:
        raise NoUpdatedReleasesError
    return res


def get_page(link: URL, params: Optional[dict] = None) -> BeautifulSoup:
    """Return a page."""
    site = requests.get(link, params)
    return BeautifulSoup(site.text, 'html.parser')


def download(
    filename: str,
    link: URL,
    *,
    download_bar: bool = True,
    text: str = 'Downloading...',
    text_end: str = '\n',
) -> None:
    """Downloads a file.

    Prints the text to the progress bar or prints the text if it is disabled or
    information about the size of the downloaded file was not received.
    """
    response = requests.get(link, stream=True)
    size = response.headers.get('Content-Length')
    if size is None or not download_bar:
        print(text, end=text_end)
        with open(filename, 'xb') as f:
            f.write(response.content)
    else:
        size = int(size)
        with Progress(transient=True) as progress:
            task = progress.add_task(text, total=100)
            with open(filename, 'xb') as f:
                for data in response.iter_content(chunk_size=size // 100):
                    f.write(data)
                    progress.update(task, advance=1)
