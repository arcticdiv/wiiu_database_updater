from dataclasses import dataclass
from typing import Any, Dict, Optional

from nus_tools import ids
from nus_tools.region import Region

from .jsontype import DatabaseJsonType


@dataclass
class Title:
    '''
    Represents a title in the database

    Titles are considered equal if they have the same titleID, version and region
    '''

    title_id: ids.TitleID
    eshop_id: str = ''
    icon_url: str = ''
    name: str = ''
    platform: int = 0
    product_code: Optional[str] = None
    region: Optional[Region] = None
    size: int = -1
    preload: bool = False
    version: Optional[int] = None
    disc_only: bool = False

    @classmethod
    def from_json_obj(cls, obj: Dict[str, Any], json_type: DatabaseJsonType) -> 'Title':
        '''
        Creates a :class:`Title` object from the given json object, associating
        it with the specified json file type
        '''

        title = cls(
            ids.TitleID(obj['TitleId']),
            obj['EshopId'],
            obj['IconUrl'],
            obj['Name'],
            obj['Platform'],
            obj['ProductCode'],
            Region[obj['Region']] if obj['Region'] and obj['Region'] != 'N/A' else None,
            int(obj['Size']),
            obj['PreLoad'],
            int(obj['Version']) if obj['Version'] else None,
            obj['DiscOnly']
        )
        title.json_type = json_type
        return title

    def to_json_obj(self) -> Dict[str, Any]:
        '''
        Creates a valid json object based on this :class:`Title` object
        '''

        return {
            'EshopId': self.eshop_id,
            'IconUrl': self.icon_url,
            'Name': self.name,
            'Platform': self.platform,
            'ProductCode': self.product_code,
            'Region': self.region.name if self.region is not None else '',
            'Size': str(self.size),
            'TitleId': str(self.title_id),
            'PreLoad': self.preload,
            'Version': str(self.version) if self.version is not None else '',
            'DiscOnly': self.disc_only
        }

    @property
    def json_type(self) -> DatabaseJsonType:
        if not hasattr(self, '_json_type'):
            self._json_type = DatabaseJsonType.from_title_id(self.title_id)
        return self._json_type

    @json_type.setter
    def json_type(self, value: DatabaseJsonType) -> None:
        self._json_type = value

    def __hash__(self) -> int:
        return hash((self.title_id, self.version, self.region))

    def __eq__(self, other):
        return (self.title_id, self.version, self.region) == (other.title_id, other.version, other.region)


class TitleNoRegionWrap:
    '''
    Wraps a :class:`Title` object, without taking title regions into
    consideration when hashing/checking equality
    '''

    def __init__(self, title: Title):
        self.title = title

    def __hash__(self):
        return hash((self.title.title_id, self.title.version))

    def __eq__(self, other):
        return (self.title.title_id, self.title.version) == (other.title.title_id, other.title.version)
