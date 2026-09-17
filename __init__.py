# MusicBrainz Picard plugin to add an ~instruments tag.
# Copyright (C) 2019 David Mandelberg
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Converted for use with Picard v3 by Bob Swift

from collections.abc import Generator

from picard.plugin3.api import (
    Metadata,
    PluginApi,
    Track,
)


def _iterate_instruments(instrument_list: str) -> Generator[str, None, None]:
    """Yields individual instruments from a string listing them.

    Args:
        instrument_list: List of instruments in the form 'A, B and C'.
    """
    remaining = instrument_list
    while remaining:
        instrument, _sep, remaining = remaining.partition(', ')
        if not remaining:
            instrument, _sep, remaining = instrument.partition(' and ')
            if ' and ' in remaining:
                raise ValueError(f"Instrument list contains multiple 'and's: {instrument_list}")
        yield instrument


def _strip_instrument_prefixes(instrument: str) -> str | None:
    """Returns the instrument name without qualifying prefixes, or None.

    Args:
        instrument: Potentially prefixed instrument name, e.g., 'solo bassoon'.

    Returns:
        The instrument name with all prefixes stripped, or None if there's nothing
        other than prefixes. The all-prefixes case can happen with relationships
        like 'guest performer'.
    """
    instrument_prefixes = {
        'additional',
        'guest',
        'solo',
    }
    remaining = instrument
    while remaining:
        prefix, sep, remaining = remaining.partition(' ')
        if prefix not in instrument_prefixes:
            return ''.join((prefix, sep, remaining))
    return None


def add_instruments(
    api: PluginApi, _track: Track, metadata: Metadata, _track_node: dict, _release_node: dict | None = None
):
    """Adds a multi-value variable listing the instruments and vocals from the performer:* tags.

    Args:
        api (PluginApi): The plugin API object.
        _track (Track): The Track object to use for the processing.
        metadata (Metadata): Metadata object for the album.
        _track_node (dict): Dictionary of track data from MusicBrainz api.
        _release_node (dict): Dictionary of release data from MusicBrainz api.
    """
    key_prefix = 'performer:'
    instruments = set()
    for key in metadata.keys():
        if not key.startswith(key_prefix):
            continue
        try:
            for instrument in _iterate_instruments(key[len(key_prefix) :]):
                instrument = _strip_instrument_prefixes(instrument)
                if instrument:
                    instruments.add(instrument)
        except ValueError as e:
            api.logger.error(f"{e}")
    if instruments:
        metadata['~instruments'] = sorted(instruments)


def enable(api: PluginApi):
    """Called when plugin is enabled."""
    api.register_track_metadata_processor(add_instruments, priority=100)

    api.register_script_variable(
        name="_instruments",
        documentation=api.tr(
            "variable.instruments",
            "All track instruments and vocals from the `performer:*` tags as a multi-value variable.",
        ),
        is_multi_value=True,
        is_from_mb=True,
    )
