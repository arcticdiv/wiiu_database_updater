import os
import json
import logging
import collections
from typing import Dict, List, Optional

from nus_tools.region import Region

from .jsontype import DatabaseJsonType
from .title import Title, TitleNoRegionWrap


TitleSet = Dict[Title, None]  # using a dict with `None` values to emulate an ordered set

_logger = logging.getLogger(__name__)


class Database:
    # main title database
    _titles: Dict[DatabaseJsonType, TitleSet]
    # additional map without taking regions into account, reduces O(n^2) complexity to approx. O(n) later on
    _titles_noregion: Dict[DatabaseJsonType, Dict[TitleNoRegionWrap, TitleSet]]

    def __init__(self, directory: str):
        self.directory = directory
        self._titles = {type: {} for type in DatabaseJsonType}
        self._titles_noregion = {type: collections.defaultdict(lambda: {}) for type in DatabaseJsonType}

    def read_all(self) -> None:
        for type in DatabaseJsonType:
            self._read(type)

    def write_all(self, directory: Optional[str] = None) -> None:
        for type in DatabaseJsonType:
            self._write(type, directory)

    def _read(self, type: DatabaseJsonType) -> None:
        with open(os.path.join(self.directory, type.filename), 'r') as f:
            data = json.load(f)

        for o in data:
            self.add_title(Title.from_json_obj(o, type))

        _logger.info(f'read {len(data):>5} titles from {type.filename}')

    def _write(self, type: DatabaseJsonType, directory: Optional[str]) -> None:
        directory = directory if directory is not None else self.directory
        os.makedirs(directory, exist_ok=True)

        serialized = [t.to_json_obj() for t in self._titles[type]]

        json_str = json.dumps(serialized, indent=2)
        json_str = json_str.replace('/', '\\/')  # escape forward slashes - not required, but the original files did it as well
        with open(os.path.join(directory, type.filename), 'w', newline='') as f:
            f.write(json_str)

        _logger.info(f'wrote {len(serialized):>5} titles to {type.filename}')

    def add_title(self, title: Title, overwrite: bool = False) -> None:
        db = self._titles[title.json_type]
        db_noregion = self._titles_noregion[title.json_type][TitleNoRegionWrap(title)]

        if title in db:
            if overwrite:
                del db[title]
                del db_noregion[title]
            else:
                return

        db[title] = None
        db_noregion[title] = None

    def fixup_regions(self) -> None:
        for json_type in (DatabaseJsonType.GAMES, DatabaseJsonType.GAMES_3DS, DatabaseJsonType.GAMES_WII, DatabaseJsonType.INJECTIONS):
            db = self._titles[json_type]
            db_noregion = self._titles_noregion[json_type]

            for matching_titles in db_noregion.values():
                if len(matching_titles) < 2:
                    # nothing to be done for no/one title
                    continue

                title_all = next((t for t in matching_titles if t.region == Region.ALL), None)
                if title_all:
                    # if title with 'ALL' region exists, remove other titles
                    log_msg = 'found title with \'ALL\' region, removing other related titles'
                elif {t.region for t in matching_titles} == {Region.EUR, Region.USA, Region.JPN, Region.KOR}:
                    # if titles for all regions exist, modify one and remove the others
                    assert len(matching_titles) == 4  # if this fails, someting probably went very wrong
                    title_all = next(iter(matching_titles))
                    title_all.region = Region.ALL
                    log_msg = 'found titles for all regions, merging into one'
                else:
                    continue

                _logger.info(f'{log_msg} (other regions: {",".join((t.region.name if t.region else "?") for t in matching_titles if t is not title_all)})')

                if title_all:
                    # remove other titles from database
                    for title in matching_titles:
                        if title is not title_all:
                            del db[title]
                    # clear, reinsert 'ALL' title
                    matching_titles.clear()
                    matching_titles[title_all] = None
                    continue

    def __contains__(self, title):
        if not isinstance(title, Title):
            return False
        return title in self._titles[title.json_type]
