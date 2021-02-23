"""Progress widgets.

This module exports the following class:
    TransferSpeedColumn2  Renders human readable transfer speed.

This module exports the following function:
    binary  Convert a file size (in bytes) to a string.
"""

from rich.filesize import _to_str, decimal
from rich.progress import Task, TransferSpeedColumn
from rich.text import Text

__all__ = ['binary', 'TransferSpeedColumn2']


def binary(size: int) -> str:
    """Convert a file size (in bytes) to a string.

    Example:
        >>> binary(30000)
        '29.3 KiB'
        >>> binary(489175685241)
        '455.6 GiB'
    """
    return _to_str(
        size, ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'), 1024
    )


class TransferSpeedColumn2(TransferSpeedColumn):
    """Renders human readable transfer speed."""

    def __init__(self, binary_units: bool = False) -> None:
        TransferSpeedColumn.__init__(self)
        self.binary_units = binary_units

    def render(self, task: Task) -> Text:
        """Show data transfer speed."""
        speed = task.speed
        if speed is None:
            return Text("?", style='progress.data.speed')
        data_speed = (
            binary(int(speed)) if self.binary_units else decimal(int(speed))
        )
        return Text(f"{data_speed}/s", style='progress.data.speed')
