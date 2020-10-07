"""Provides classes and functions for interacting with the 'animevost.org' site.

This module exports the following classes:
    Release
    AnimevostRelease
    Animevost
    AnimevostSearchQuery
    AnimevostPlaylist

This module exports the following function:
    get_recent_releases  Return a list of the latest releases from the animevost
                         site.
"""

import os
import pickle
import re
from functools import total_ordering
from typing import Iterable, List, NoReturn, Optional, Tuple, Union


import requests

from anime_downloader import library
from anime_downloader.exceptions import *
from anime_downloader.library import URL

DEFAULT_PATH_TO_DB = os.path.expanduser('~/.config/anime-downloader/db')
ANIMEVOST_LINK = 'https://animevost.org'


class Release(library.Release):
    """Release wrapper that implement the _get_title method."""

    @staticmethod
    def _get_title(link: URL) -> str:
        """Return the name of the release."""
        animevost = library.get_page(link)
        animevost = animevost.find(class_='shortstoryHead')
        return str(animevost.h1.string).strip()


class Anime:
    """
    Instance of this class contains the release and playlist attributes, which
    are implemented as AnimevostRelease and AnimevostPlaylist.
    """

    def __init__(
        self,
        search_query_text: str,
        *,
        text_for_get_user_choice: str = "Enter the release number: ",
    ) -> None:
        """Print the search result and the prompt."""
        self._search_query_text = search_query_text
        self._text_for_get_user_choice = text_for_get_user_choice
        self.release = self._get_user_choice()
        self.playlist = Playlist(self._get_id(self.release.link))

    def update(self) -> None:
        """Update the release playlist and title.

        If the release playlist has not been changed then its name will not be
        updated (done for optimization).
        """
        tmp_playlist = self.playlist.copy()
        self.playlist.update()
        if tmp_playlist != self.playlist:
            self.release.update_title()

    def save_to_db(self, path_to_db: str = DEFAULT_PATH_TO_DB) -> None:
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

    def delete_from_db(self, path_to_db: str = DEFAULT_PATH_TO_DB) -> None:
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

    def _print_search_result(self) -> None:
        """Print the result of the search query."""
        self._search_result = SearchQuery(self._search_query_text)
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
    def _get_id(link: URL) -> int:
        """Return the id of the cut."""
        return int(re.search(r'(?<=/)\d+(?=-)', link).group())

    def __str__(self) -> str:
        clsname = self.__class__.__name__
        return f"<{clsname}.{self.release}>"

    def __repr__(self) -> str:
        clsname = self.__class__.__name__
        return f"{clsname}('{self._search_query_text}') <{self.release}>"

    def __eq__(self, other: 'Anime') -> bool:
        if ((self._search_query_text, self._text_for_get_user_choice)
                == (other._search_query_text, self._text_for_get_user_choice)):
            return True
        return False

    def __ne__(self, other: 'Anime') -> bool:
        return not self.__eq__(other)


class SearchQuery:
    """Represent a search query object. This type object is immutable.

    Instance of this class contain a releases attribute which contains a tuple
    containing objects of type AnimevostRelease.
    """

    def __init__(self, search_query_text: str, /) -> None:
        object.__setattr__(
            self, 'releases', self._get_search_query_results(search_query_text)
        )

    @staticmethod
    def _get_search_query_results(search_query_text: str, /) -> Tuple[Release]:
        """Return a tuple of releases.

        Raises SearchQueryDidNotReturnAnyResultsError if search query return an
        empty release list.
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
        animevost = library.get_page(ANIMEVOST_LINK, search_query_params)
        animevost = animevost(class_='shortstory')

        links = [str(i.a['href']) for i in animevost]
        titles = [str(i.a.string) for i in animevost]
        res = []
        for link, title in zip(links, titles):
            res.append(Release(link, title))
        if not res:
            raise SearchQueryDidNotReturnAnyResultsError
        return tuple(res)

    def __bool__(self) -> bool:
        return bool(self.releases)

    def __setattr__(self, key, value) -> NoReturn:
        class_name = self.__class__.__name__
        if key in dir(self):
            raise AttributeError(
                f"'{class_name}' object attribute '{key}' is read-only"
            )
        raise AttributeError(f"'{class_name}' object has no attribute '{key}'")

    def __len__(self) -> int:
        return len(self.releases)

    def __getitem__(self, key: Union[int, slice]) -> Union[Release, Tuple[Release]]:
        return self.releases[key]

    def __setitem__(self, key, value) -> NoReturn:
        class_name = self.__class__.__name__
        raise TypeError(f"'{class_name}' object does not support item assignment")

    def __iter__(self) -> Iterable[Release]:
        return iter(self.releases)


@total_ordering
class Playlist(library.Playlist):
    """Instance of this class contain an id attribute that depends on the release.

    This class exports the following methods:
        download_episode   Download a episode.
        download_episodes  Download a episodes.
        update             Update the playlist.
        copy               Return a shallow copy of the AnimevostPlaylist.
    """

    def __init__(self, id: int, *, playlist: Optional[Iterable[URL]] = None) -> None:
        self.id = id
        if playlist is None:
            library.Playlist.__init__(self, self._get_links_to_episodes(), copy=False)
        else:
            self.playlist = list(playlist)
        self.is_modified_after_update = True

    def download_episode(
        self,
        episode: Optional[int] = None,
        downloads: str = '~/Downloads',
        *,
        mkdir: bool = False,
    ) -> None:
        """Download the specified episode from the playlist."""
        downloads = os.path.expanduser(downloads)
        if mkdir:
            downloads = os.path.join(downloads, str(self.id))
            if not os.path.exists(downloads):
                os.mkdir(downloads)

        link = self[episode]
        episode = self.index(link)
        library.download(
            os.path.join(downloads, f'{self.id}_{episode}.mp4'),
            link,
            text=f"Downloading episode {episode}",
        )

    def download_episodes(
        self,
        episode_start: Optional[int] = None,
        episode_stop: Optional[int] = None,
        downloads: str = '~/Downloads',
        *,
        mkdir: bool = True,
    ) -> None:
        """Download the specified episodes from the playlist."""
        downloads = os.path.expanduser(downloads)
        if mkdir:
            downloads = os.path.join(downloads, str(self.id))
            if not os.path.exists(downloads):
                os.mkdir(downloads)

        for link in self[episode_start:episode_stop]:
            episode = self.index(link)
            library.download(
                os.path.join(downloads, f'{self.id}_{episode}.mp4'),
                link,
                text=f"Downloading episode {episode}",
            )

    def update(self) -> None:
        """Update the playlist."""
        playlist_before = self.playlist
        library.Playlist.__init__(self, self._get_links_to_episodes(), copy=False)
        self.is_modified_after_update = (
            True if self.playlist != playlist_before else False
        )

    def copy(self) -> 'Playlist':
        """Return a shallow copy of the AnimevostPlaylist."""
        copy = Playlist(self.id, playlist=self.playlist)
        copy.is_modified_after_update = self.is_modified_after_update
        return copy

    def _get_links_to_episodes(self) -> List[URL]:
        """Return a list of episodes links."""
        # FIXME: 'Этот замечательный мир! (фильм)'
        #  ValueError: invalid literal for int() with base 10: 'Фильм'
        links_to_episodes = requests.post(
            'https://api.animevost.org/v1/playlist', {'id': self.id}
        ).json()
        res = {}
        for i in links_to_episodes:
            episode = int(re.sub(r' серия', '', i['name']))
            link = i['hd']
            res[episode] = link
        return [res[i] for i in sorted(res)]

    def __lt__(self, other: 'Playlist') -> bool:
        return (self.id, self.playlist) < (self.id, other.playlist)

    def __eq__(self, other: 'Playlist') -> bool:
        return (self.id, self.playlist) == (other.id, other.playlist)


def get_recent_releases() -> List[Release]:
    """Return a list of the latest releases from the animevost site."""
    animevost = library.get_page(ANIMEVOST_LINK)
    animevost = animevost.find(class_='raspis raspis_fixed')
    animevost = animevost('a')

    links = [str(i['href']) for i in animevost]
    titles = [str(i.string) for i in animevost]
    res = []
    for link, title in zip(links, titles):
        res.append(Release(link, title))
    return res
