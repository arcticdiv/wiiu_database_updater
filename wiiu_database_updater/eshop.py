import itertools
from typing import List, Optional

from nus_tools import ids
from nus_tools.sources import \
    Samurai, Ninja, IDBEServer, CertType, \
    TagayaCDN, TagayaNoCDN, \
    ContentServerCDN
from nus_tools.region import Region
from reqcli.errors import ResponseStatusError
from reqcli.source import SourceConfig

from .title import Title
from .database import Database, DatabaseJsonType


class EShop:
    def __init__(self, db: Database, client_cert: CertType, reload: bool, source_config: Optional[SourceConfig] = None):
        self._db = db
        self._client_cert = client_cert
        self._reload = reload
        self._source_config = source_config

    def get_titles(self, region: Region, shop_id: int) -> None:
        # shop_id=1 for 3DS, shop_id=2 for WiiU
        samurai = Samurai(region, shop_id, None, self._source_config)
        ninja = Ninja(region, self._client_cert, self._source_config)
        idbe = IDBEServer('wup', self._source_config)  # platform does not matter

        num_titles = samurai.get_title_count(skip_cache_read=self._reload)
        title_iterable = itertools.chain.from_iterable(lst.titles for lst in samurai.get_all_title_lists(skip_cache_read=self._reload))

        for i, title in enumerate(title_iterable):
            print(f'{i + 1}/{num_titles}', title.content_id)

            # skip retail only
            if not title.release_date_eshop and not title.sales_eshop:
                continue

            # skip "Wii U builtin software", currently only matches TVii
            if title.platform.id == 143:
                continue

            ec_info = ninja.get_ec_info(title.content_id)

            try:
                title_regions = self._get_regions(idbe, ec_info.title_id)
            except ResponseStatusError as e:
                if e.status != 403:
                    raise
                # default to eshop region if IDBE doesn't exist
                title_regions = [region]

            # add title for each region
            for title_region in title_regions:
                self._db.add_title(Title(
                    ec_info.title_id,
                    title.content_id,
                    title.icon_url or '',
                    title.name,
                    title.platform.id,
                    title.product_code.split('-')[-1],  # WUP-N-ALZE -> ALZE
                    title_region,
                    ec_info.content_size,
                    False,
                    None,
                    ec_info.content_size == 0
                ))

    def get_wiiu_updates(self, start_list_version: int = 1) -> int:
        tagaya_direct = TagayaNoCDN(self._source_config)
        latest_list_version = tagaya_direct.get_latest_updatelist_version().latest

        ccs = ContentServerCDN(self._source_config)
        tagaya_cdn = TagayaCDN(self._source_config)
        for list_version in range(start_list_version, latest_list_version + 1):
            try:
                update_list = tagaya_cdn.get_updatelist(list_version).updates
            except ResponseStatusError as e:
                # ignore 403 received for some lists
                if e.status == 403:
                    continue
                raise

            for update_id, update_version in update_list:
                if not update_id.is_update:
                    # update lists also contain games for some reason, just skip them
                    continue

                # create update title
                update_title = Title(
                    title_id=update_id,
                    version=update_version
                )
                # no need to calculate sizes for titles already present in db
                if update_title not in self._db:
                    self._add_size(ccs, update_title, False)
                    self._db.add_title(update_title)

        return latest_list_version

    def get_wiiu_dlcs(self) -> None:
        ccs = ContentServerCDN(self._source_config)

        for game in self._db._titles[DatabaseJsonType.GAMES]:
            # only check WiiU games
            if game.title_id.type != ids.TitleType.GAME_WIIU:
                continue

            # some comments:
            #  - this approach isn't great, because it's essentially bruteforcing TMDs,
            #    and nonexistent TMDs (guaranteed CDN cache misses) take 1-2 seconds each
            #  - the /aocs samurai endpoint would seem like a good candidate, but from
            #    what I've seen it isn't always accurate (i.e. doesn't return DLCs when it should) :/
            #  - unlike updates, this is *not* skipping DLCs already present in the db,
            #    since sizes might have changed due to new versions

            # create DLC title
            dlc_title = Title(
                title_id=game.title_id.dlc
            )
            try:
                if dlc_title in self._db:
                    # if dlc already exists, just try to update the size of the existing dlc
                    # TODO: (this next line is pretty inefficient)
                    dlc_title = next(t for t in self._db._titles[DatabaseJsonType.DLCS] if t == dlc_title)
                    self._add_size(ccs, dlc_title, self._reload)
                else:
                    # if dlc doesn't exist, get size and add title to db
                    self._add_size(ccs, dlc_title, self._reload)
                    self._db.add_title(dlc_title, overwrite=True)
            except ResponseStatusError as e:
                # if a 404 is returned, there is no DLC
                if e.status == 404:
                    continue
                raise

    def _get_regions(self, idbe: IDBEServer, title_id: ids.TTitleIDInput) -> List[Region]:
        region_codes = idbe.get_idbe(title_id).data.regions

        if region_codes.ALL:
            # if region codes match 'ALL', we're done
            return [Region.ALL]
        else:
            # get list of region names for provided title ID
            region_codes = [k for k, v in region_codes.items() if v and not k.startswith('_')]

            # map region codes to (known) regions
            regions = []
            for region_code in region_codes:
                try:
                    regions.append({
                        'JP': Region.JPN,
                        'US': Region.USA,
                        'EU': Region.EUR,
                        'KO': Region.KOR
                    }[region_code])
                except KeyError:
                    pass  # ignore others

            if len(regions) == 0:
                raise RuntimeError(f'no known region found for title ID {title_id}')
            return regions

    def _add_size(self, ccs: ContentServerCDN, title: Title, skip_cache_read: bool) -> None:
        # get TMD for title (+ version)
        version = title.version if title.title_id.is_update else None
        tmd = ccs.get_tmd(title.title_id, version, skip_cache_read=skip_cache_read).data
        # sanity check
        if version is not None:
            assert tmd.title_version == version

        # calculate size based on contents
        title.size = sum(c.size for c in tmd.contents)
