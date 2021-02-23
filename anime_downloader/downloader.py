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

"""Core downloader.

This module exports the following classes:
    AbstractDownloader  An abstract downloader class.
    Downloader  An downloader class.
"""

import os
import sys
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable
from urllib.parse import unquote, urlsplit

import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn
)

from anime_downloader.progress_widgets import TransferSpeedColumn2

__all__ = ['AbstractDownloader', 'Downloader']

progress = Progress(
    TextColumn('[green]{task.fields[file_name]}'),
    BarColumn(bar_width=None),
    '[progress.percentage]{task.percentage:>3.1f}%',
    DownloadColumn(binary_units=True),
    TransferSpeedColumn2(binary_units=True),
    TimeRemainingColumn(),
)


class AbstractDownloader(ABC):
    """An abstract downloader class.

    Instance of this class contain the `urls`, `path_to_downloads`,
    `continue_` attributes.
    """

    def __init__(
        self,
        urls: Iterable,
        path_to_downloads: str,
        continue_: bool = True,
        start: bool = True,
    ) -> None:
        self.urls = list(urls)
        self.path_to_downloads = os.path.abspath(
            os.path.expanduser(path_to_downloads)
        )
        self.continue_ = continue_
        if start:
            self.download()

    def download(self, **kwargs) -> None:
        """Download the files listed in the `self.urls` attribute.

        If the `self.continue_` attribute is set to `True` then download
        of the file will continue instead of starting from the
        beginning.
        """
        self._stage_1_download(**kwargs)
        self._stage_2_rename_temp_file_name_to_file_name()

    @abstractmethod
    def _stage_1_download(self, **kwargs) -> None:
        """
        Download the files listed in the `self.urls` attribute with the
        '.part' suffix.

        If the `self.continue_` attribute is set to `True` then download
        of the file will continue instead of starting from the
        beginning.
        """

    def _stage_2_rename_temp_file_name_to_file_name(self) -> None:
        """Rename temp file name to file name."""
        for url in self.urls:
            path_to_temp_file = self.get_path_to_temp_file(url)
            path_to_file = self.get_path_to_file(url)
            self._rename(path_to_temp_file, path_to_file)

    @staticmethod
    def get_file_name(url: str) -> str:
        """Return the file name based on URL."""
        url_path = urlsplit(url).path
        file_name = os.path.basename(unquote(url_path))
        if (
            os.path.basename(file_name) != file_name
            or unquote(os.path.basename(url_path))
        ) != file_name:
            raise ValueError(f"can not get file name from '{url}'")
        return file_name

    def get_path_to_file(self, url: str) -> str:
        """Return the path to the file based on URL."""
        file_name = self.get_file_name(url)
        return os.path.join(self.path_to_downloads, file_name)

    def get_temp_file_name(self, url: str) -> str:
        """Return the name of the temp file based on URL."""
        file_name = self.get_file_name(url)
        return f'{file_name}.part'

    def get_path_to_temp_file(self, url: str) -> str:
        """Return the path to the temp file based on URL."""
        temp_file_name = self.get_temp_file_name(url)
        return os.path.join(self.path_to_downloads, temp_file_name)

    def get_temp_file_size(self, url: str) -> int:
        """Return the size of a temp file based on URL."""
        path_to_temp_file = self.get_path_to_temp_file(url)
        return os.path.getsize(path_to_temp_file)

    _rename = os.rename


class Downloader(AbstractDownloader):
    """An downloader class.

    Instance of this class contain the `urls`, `path_to_downloads`,
    `continue_` attributes.
    """

    def download(self, **kwargs) -> None:
        """Download the files listed in the `self.urls` attribute.

        If the `self.continue_` attribute is set to `True` then download
        of the file will continue instead of starting from the
        beginning.

        For valid parameters for `**kwargs`, see the documentation for
        `requests.get`.
        """
        AbstractDownloader.download(self, **kwargs)

    def _stage_1_download(self, max_workers: int = 4, **kwargs) -> None:
        """
        Download the files listed in the `self.urls` attribute with the
        '.part' suffix.

        If the `self.continue_` attribute is set to `True` then download
        of the file will continue instead of starting from the
        beginning.

        For valid parameters for `**kwargs`, see the documentation for
        `requests.get`.
        """
        with progress:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for url in self.urls:
                    file_name = self.get_file_name(url)
                    task_id = progress.add_task(
                        'Download.', file_name=file_name, start=True
                    )
                    pool.submit(self._copy_url, task_id, url, **kwargs)

    def _copy_url(self, task_id: TaskID, url: str, **kwargs) -> None:
        """Copies the URL while showing the progress bar.

        The task must not be started, otherwise the progress bar will
        appear before downloading.

        For valid parameters for `**kwargs`, see the documentation for
        `requests.get`.
        """
        response = self._get_response(url, **kwargs)
        path_to_temp_file = self.get_path_to_temp_file(url)
        temp_file_flags = 'ab' if self.continue_ else 'wb'
        final_file_size = self._get_response_size(response)

        progress.update(task_id, total=final_file_size)
        progress.start_task(task_id)
        with open(path_to_temp_file, temp_file_flags) as temp_file:
            # 2 ** 20 B = 1048576 B = 1 Mibit
            for data in response.iter_content(2 ** 20):
                temp_file.write(data)
                temp_file.flush()
                progress.update(task_id, advance=len(data))

    def _get_response(self, url: str, **kwargs) -> requests.Response:
        """Return the response.

        For valid parameters for `**kwargs`, see the documentation for
        `requests.get`.
        """
        headers = {}
        path_to_temp_file = self.get_path_to_temp_file(url)
        if self.continue_ and os.path.exists(path_to_temp_file):
            temp_file_size = self.get_temp_file_size(url)
            headers.update(Range=f'bytes={temp_file_size}-')

        response = requests.get(url, headers=headers, stream=True, **kwargs)
        return response

    @staticmethod
    def _get_response_size(response: requests.Response) -> int:
        """Return the size of the response.

        Raises `KeyError` if the 'Content-Length' field is missing in
        the headers.  Raises `ValueError` if the 'Content-Length' field
        contains a non-integer number.
        """
        return int(response.headers['Content-Length'])

    @staticmethod
    def _rename(src, dst, *, src_dir_fd=None, dst_dir_fd=None) -> None:
        """Rename the file or directory `src` to `dst`.

        This method uses the `os.rename` function and catches the
        `OSError` exception and prints the exception message to
        `sys.stderr`.
        """
        try:
            os.rename(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)
        except OSError as e:
            print(e, file=sys.stderr)
