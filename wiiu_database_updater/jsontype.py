from enum import Enum, auto

from nus_tools import ids


class DatabaseJsonType(Enum):
    '''
    Indicates a :class:`Title`'s origin/target .json file
    '''

    CUSTOMS = auto()
    DLCS = auto()
    DLCS_3DS = auto()
    GAMES = auto()
    GAMES_3DS = auto()
    GAMES_WII = auto()
    INJECTIONS = auto()
    UPDATES = auto()
    UPDATES_3DS = auto()

    @property
    def filename(self):
        return {
            DatabaseJsonType.CUSTOMS: 'customs.json',
            DatabaseJsonType.DLCS: 'dlcs.json',
            DatabaseJsonType.DLCS_3DS: 'dlcs3ds.json',
            DatabaseJsonType.GAMES: 'games.json',
            DatabaseJsonType.GAMES_3DS: 'games3ds.json',
            DatabaseJsonType.GAMES_WII: 'gamesWii.json',
            DatabaseJsonType.INJECTIONS: 'injections.json',
            DatabaseJsonType.UPDATES: 'updates.json',
            DatabaseJsonType.UPDATES_3DS: 'updates3ds.json'
        }[self]

    @staticmethod
    def from_title_id(title_id: ids.TitleID) -> 'DatabaseJsonType':
        if title_id.type.platform == ids.TitlePlatform.WII:
            return DatabaseJsonType.GAMES_WII
        else:
            try:
                return {
                    ids.TitleType.GAME_3DS: DatabaseJsonType.GAMES_3DS,
                    ids.TitleType.UPDATE_3DS: DatabaseJsonType.UPDATES_3DS,
                    ids.TitleType.DLC_3DS: DatabaseJsonType.DLCS_3DS,
                    ids.TitleType.DSIWARE_3DS: DatabaseJsonType.GAMES_3DS,
                    ids.TitleType.GAME_WIIU: DatabaseJsonType.GAMES,
                    ids.TitleType.UPDATE_WIIU: DatabaseJsonType.UPDATES,
                    ids.TitleType.DLC_WIIU: DatabaseJsonType.DLCS
                }[title_id.type]
            except KeyError:
                raise RuntimeError(f'title ID {title_id} not associated with any json file')
