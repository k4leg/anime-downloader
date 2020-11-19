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

"""Provides classes and functions for interacting with the 'animevost.org' site.

This module exports the following classes:
    Anime
    SearchQuery

This module exports the following function:
    get_recent_anime  Return a list of the latest releases from the animevost
                      site.
"""

__all__ = ['Anime', 'SearchQuery', 'get_recent_anime']

import re
from typing import List, Optional, Tuple

import requests

from anime_downloader import library
from anime_downloader.exceptions import *

URL = str
ANIMEVOST_LINK = 'https://animevost.org'


class Anime(library.Anime):
    def __init__(self, link: URL, title: Optional[str] = None) -> None:
        self.link = link
        self.title = self._get_title() if title is None else title
        self.id = self._get_id()
        self.update_playlist()

    def update_playlist(self) -> None:
        """Update `self.playlist`.

        Sets `self.is_modified_after_update` to `True` if `self.playlist` has
        been updated else `False`.
        """
        playlist = library.Playlist(self._get_links_to_episodes())
        try:
            self.is_modified_after_update = self.playlist != playlist
        except AttributeError:
            self.is_modified_after_update = True
        self.playlist = playlist

    def _get_title(self) -> str:
        """Return the title."""
        page = library.get_page(self.link)
        title = page.find(class_='shortstoryHead')
        title = str(title.h1.string).strip()
        return _format_title(title)

    def _get_id(self) -> int:
        """Return the id."""
        try:
            return int(re.search(r'(?<=/)\d+(?=-)', self.link).group())
        except AttributeError:
            raise LinkHasNoIDError(self.link) from None

    def _get_links_to_episodes(self) -> List[URL]:
        """Return a list of episodes links."""
        links_to_episodes = requests.post(
            'https://api.animevost.org/v1/playlist', {'id': self.id}
        ).json()
        res = {}
        for i in links_to_episodes:
            try:
                episode = int(re.search(r'\d+', i['name']).group())
            except AttributeError:
                episode = float('-inf')
            link = i['hd']
            res[episode] = link
        return [res[i] for i in sorted(res)]


class SearchQuery(library.SearchQuery):
    def _get_search_query_results(self) -> Tuple[Anime, ...]:
        """Return a tuple of releases.

        Raises `SearchQueryDidNotReturnAnyResultsError` if search query return an
        empty release list.
        """
        if len(self._search_query_text) < 4:
            raise SearchQueryLenError

        search_query_params = {
            'do': 'search',
            'subaction': 'search',
            'search_start': '0',
            'full_search': '0',
            'result_from': '1',
            'story': self._search_query_text,
        }
        animevost = library.get_page(ANIMEVOST_LINK, search_query_params)
        animevost = animevost(class_='shortstory')

        links = [str(i.a['href']) for i in animevost]
        titles = [str(i.a.string) for i in animevost]
        res = []
        for link, title in zip(links, titles):
            if self._format:
                title = _format_title(title)
            res.append(Anime(link, title))
        if not res:
            raise SearchQueryDidNotReturnAnyResultsError
        return tuple(res)


def get_recent_anime(*, format: bool = True) -> List[Anime]:
    """Return a list of the latest releases from the animevost site."""
    animevost = library.get_page(ANIMEVOST_LINK)
    animevost = animevost.find(class_='raspis raspis_fixed')
    animevost = animevost('a')

    links = [str(i['href']) for i in animevost]
    titles = [str(i.string) for i in animevost]
    res = []
    for link, title in zip(links, titles):
        if format:
            title = _format_title(title)
        res.append(Anime(link, title))
    return res


def _format_title(title: str) -> str:
    """Formats the title.

    Example:
    >>> _format_title('Бездарная Нана / Munou na Nana")
    'Бездарная Нана'
    """
    return re.sub(' /.*', '', title)
