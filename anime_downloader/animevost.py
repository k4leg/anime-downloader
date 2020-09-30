"""Provides classes and functions for interacting with the 'animevost.org' site.

This module exports the following classes:
    Release
    AnimevostRelease
    Animevost
    AnimevostSearchQuery
    AnimevostPlaylist

This module exports the following function:
    get_recent_releases Return a list of the latest releases from the
                        animevost site.
"""

import os
import pickle
import re
from abc import ABCMeta, abstractmethod
from typing import Optional, List, Tuple

import requests

from . import library
from .exceptions import *

PATH_TO_CONFIG_DIR = os.path.expanduser('~/.config/anime-downloader')
try:
    os.mkdir(PATH_TO_CONFIG_DIR)
except FileExistsError:
    pass

PATH_TO_CONFIG = os.path.join(PATH_TO_CONFIG_DIR, 'config')
try:
    CONFIG = library.Config(os.path.expanduser(PATH_TO_CONFIG))
except NotEnoughArgumentsToInitializeError:
    CONFIG = library.Config(
        PATH_TO_CONFIG,
        path_to_db=os.path.join(PATH_TO_CONFIG_DIR, 'db'),
        path_to_downloads=os.popen('xdg-user-dir DOWNLOAD').read().rstrip()
    )

ANIMEVOST_LINK = 'https://animevost.org'


class Release(metaclass=ABCMeta):
    """
    Instance of this class contain the attributes of the 'link' to the release
    and the 'title' of the release.  The release name can be taken from the link
    by implementing the '_get_title' method and if the release name has been
    passed then unnecessary actions for calling the '_get_title' method are not
    done.
    """

    def __init__(self, link: str, title: Optional[str] = None, /):
        self.link = link
        self.update_title(title)

    def update_title(self, title: Optional[str] = None, /):
        """Update the release name."""
        self.title = self._get_title(self.link) if title is None else title

    @staticmethod
    @abstractmethod
    def _get_title(link: str):
        """Return the name of the release."""
        pass

    def __str__(self):
        clsname = self.__class__.__name__
        return f"{clsname}('{self.title}', '{self.link}')"


class AnimevostRelease(Release):
    """Release wrapper that implement the '_get_title' method."""

    @staticmethod
    def _get_title(link: str) -> str:
        """Return the name of the release."""
        animevost = library.get_site(link)
        animevost = animevost.find(class_='shortstoryHead')
        return str(animevost.h1.string).strip()


class Animevost:
    """
    Instance of this class contains the 'release' and 'playlist' attributes,
    which are implemented as AnimevostRelease and AnimevostPlaylist.
    """

    def __init__(
        self,
        search_query_text: str,
        /, *,
        text_for_get_user_choice: str = "Enter the release number: ",
    ):
        """Print the search result and the prompt."""
        self._search_query_text = search_query_text
        self._text_for_get_user_choice = text_for_get_user_choice
        self.release = self._get_user_choice()
        self.playlist = AnimevostPlaylist(self._get_id(self.release.link))

    def update(self):
        """Update the release playlist and title.

        If the release playlist has not been changed then its name will not be
        updated (done for optimization).
        """
        tmp_playlist = self.playlist.copy()
        self.playlist.update()
        if tmp_playlist != self.playlist:
            self.release.update_title()

    def save_to_db(self, path_to_db: str = CONFIG.path_to_db, /):
        """Save to the DB (and creates it if didn't exist) instance object."""
        try:
            with open(path_to_db, 'rb') as f:
                db: list = pickle.load(f)

            try:
                index = db.index(self)
                db.remove(self)
                db.insert(index, self)
            except ValueError:
                db.append(self)

            with open(path_to_db, 'wb') as f:
                pickle.dump(db, f)
        except FileNotFoundError:
            with open(path_to_db, 'xb') as f:
                pickle.dump([self], f)

    def delete_from_db(self, path_to_db: str = CONFIG.path_to_db, /):
        """Remove an instance object from the DB.

        Raises ObjectNotFoundInDBError if instance isn't in the DB.
        """
        with open(path_to_db, 'rb') as f:
            db: list = pickle.load(f)

        try:
            db.remove(self)
        except ValueError:
            raise ObjectNotFoundInDBError(self) from None

        with open(path_to_db, 'wb') as f:
            pickle.dump(db, f)

    def _print_search_result(self):
        """Print the result of the search query."""
        self._search_result = AnimevostSearchQuery(self._search_query_text)

        for n, release in enumerate(self._search_result, 1):
            title = release.title
            link = release.link
            print(f"{n}. {title} ({link})")

    def _get_user_choice(self) -> Release:
        """Return the user selection."""
        self._print_search_result()

        user_choice = int(input(self._text_for_get_user_choice))
        if not 0 < user_choice <= len(self._search_result):
            raise UserEnteredIncorrectDataError

        return self._search_result[user_choice - 1]

    @staticmethod
    def _get_id(link: str, /) -> int:
        """Return the id of the cut."""
        id = re.search(r'(?<=/)\d+(?=-)', link).group()
        return int(id)

    def __str__(self):
        clsname = self.__class__.__name__
        return f"<{clsname}.{self.release}>"

    def __repr__(self):
        clsname = self.__class__.__name__
        return f"{clsname}('{self._search_query_text}') <{self.release}>"

    def __eq__(self, other):
        if (self._search_query_text == other._search_query_text
                and self._text_for_get_user_choice
                == other._text_for_get_user_choice):
            return True

        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class AnimevostSearchQuery:
    """Represent a search query object. This type object is immutable.

    Instance of this class contain a 'releases' attribute which contains a
    tuple containing objects of type AnimevostRelease.
    """

    def __init__(self, search_query_text: str, /):
        self.__dict__['releases'] = self._get_search_query_results(
            search_query_text
        )

    @staticmethod
    def _get_search_query_results(
        search_query_text: str,
    ) -> Tuple[AnimevostRelease]:
        """Return a tuple of releases.

        Raises SearchQueryDidNotReturnAnyResultsError if search query return
        an empty release list.
        """
        if len(search_query_text) < 4:
            raise SearchQueryLenError

        search_query_params = {
            'do': 'search',
            'subaction': 'search',
            'search_start': '0',
            'full_search': '0',
            'result_from': '1',
            'story': search_query_text,
        }
        animevost = library.get_site(ANIMEVOST_LINK, search_query_params)
        animevost = animevost(class_='shortstory')

        links = [str(i.a['href']) for i in animevost]
        titles = [str(i.a.string) for i in animevost]

        res = []
        for link, title in zip(links, titles):
            res.append(AnimevostRelease(link, title))
        if not res:
            raise SearchQueryDidNotReturnAnyResultsError

        return tuple(res)

    def __getitem__(self, key):
        return self.releases[key]

    def __iter__(self):
        return self.releases.__iter__()

    def __len__(self):
        return len(self.releases)

    def __bool__(self):
        return bool(self.releases)

    def __setitem__(self, key, value):
        clsname = self.__class__.__name__
        raise TypeError(f"{clsname} object does not support item assignment")

    def __setattr__(self, key, value):
        clsname = self.__class__.__name__
        if key in dir(self):
            raise AttributeError(f"'{clsname}' object attribute '{key}' is"
                                 + "read-only")

        raise AttributeError(f"'{clsname}' object has no attribute '{key}'")


class AnimevostPlaylist:
    """Instance of this class contain an 'id' attribute that depends on the
    release.

    This class exports the following methods:
        download_episode    Download a episode.
        download_episodes   Download a episodes.
        update              Update the playlist.
        copy                Return a shallow copy of the AnimevostPlaylist.
    """

    def __init__(
        self,
        id: int,
        /, *,
        playlist: Optional[library.Playlist] = None,
        copy: bool = True,
    ):
        self.id = id
        self.copy_flag = copy
        if playlist is None:
            self.update()
        else:
            self.playlist = playlist.copy() if self.copy_flag else playlist
            self.is_modified_after_update = True

    def download_episode(
        self,
        episode: Optional[int] = None,
        downloads: str = '~/Downloads',
        mkdir: bool = False,
    ):
        """Download the specified episode from the playlist."""
        downloads = os.path.expanduser(downloads)
        if mkdir:
            downloads = os.path.join(downloads, str(self.id))
            if not os.path.exists(downloads):
                os.mkdir(downloads)

        link = self.playlist[episode]
        episode = self.playlist.index(link) + 1
        library.download(
            os.path.join(downloads, f'{self.id}_{episode}.mp4'),
            link,
            text=f"Downloading episode {episode}"
        )

    def download_episodes(
        self,
        episode_start: Optional[int] = None,
        episode_stop: Optional[int] = None,
        downloads: str = '~/Downloads',
        mkdir: bool = True,
    ):
        """Download the specified episodes from the playlist."""
        downloads = os.path.expanduser(downloads)
        if mkdir:
            downloads = os.path.join(downloads, str(self.id))
            if not os.path.exists(downloads):
                os.mkdir(downloads)

        for link in self.playlist[episode_start:episode_stop]:
            episode = self.playlist.index(link) + 1
            library.download(
                os.path.join(downloads, f'{self.id}_{episode}.mp4'),
                link,
                text='Downloading episode {episode}'
            )

    def update(self):
        """Update the playlist."""
        playlist = requests.post(
            'https://api.animevost.org/v1/playlist', {'id': self.id}
        ).json()
        playlist = self._get_links_to_episodes(playlist)
        playlist = library.Playlist(playlist)
        if (hasattr(self, 'playlist') and (self.playlist != playlist)
                or not hasattr(self, 'playlist')):
            self.is_modified_after_update = True
            self.playlist = playlist
        else:
            self.is_modified_after_update = False

    def copy(self):
        """Return a shallow copy of the AnimevostPlaylist."""
        return AnimevostPlaylist(
            self.id,
            playlist=self.playlist,
            copy=self.copy_flag
        )

    @staticmethod
    def _get_links_to_episodes(links_to_episodes: List[dict], /) -> list:
        """Return a list of episodes links."""
        res = {}
        for i in links_to_episodes:
            episode = int(re.sub(r' серия', '', i['name']))
            link = i['hd']
            res[episode] = link

        return [res[i] for i in sorted(res)]

    def __eq__(self, other):
        if self.id == other.id and self.playlist == other.playlist:
            return True

        return False

    def __ne__(self, other):
        return not self.__eq__(other)


def get_recent_releases() -> List[AnimevostRelease]:
    """Return a list of the latest releases from the animevost site."""
    animevost = library.get_site(ANIMEVOST_LINK)
    animevost = animevost.find(class_='raspis raspis_fixed')
    animevost = animevost('a')

    links = [str(i['href']) for i in animevost]
    titles = [str(i.string) for i in animevost]

    res = []
    for link, title in zip(links, titles):
        res.append(AnimevostRelease(link, title))

    return res
