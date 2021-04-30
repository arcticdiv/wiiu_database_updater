import logging
import argparse
from pathlib import Path

from nus_tools.config import Configuration as NUSToolsConfiguration
from nus_tools.structs import rootkey
from nus_tools.region import Region
from reqcli.source import SourceConfig

from .database import Database
from .eshop import EShop


latest_update_list_version_name = 'latest_update_list_version'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='wiiu_database_updater',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '-l', '--log-level',
        default='INFO',
        help='logging level (valid values are python\'s builtin logging levels)'
    )
    parser.add_argument(
        '-ld', '--log-level-dep',
        default='INFO',
        help='logging level for dependendencies'
    )
    parser.add_argument(
        '--root-key-file',
        default=None,
        help='path to \'Root\' public key (signing CA for TMD/Ticket files)'
    )
    parser.add_argument(
        '--ignore-last-update-list-version',
        action='store_true',
        help='ignore any stored update list version files, always start from 1'
    )
    parser.add_argument(
        '-n', '--no-reload',
        action='store_true',
        help='enable reading most responses from cache (useful for debugging)'
    )
    parser.add_argument(
        '--shop-id',
        type=int,
        default=2,
        choices=[1, 2, 3, 4],
        help='shop ID used for retrieving new titles'
    )
    parser.add_argument(
        '-r', '--ratelimit',
        dest='requests_per_second',
        type=float,
        default=2,
        help='maximum requests per host per second'
    )
    for name in ('titles', 'updates', 'dlcs'):
        parser.add_argument(
            f'--no-{name}',
            dest=f'get_{name}',
            action='store_false',
            default=True,
            help=f'don\'t retrieve new {name}'
        )

    parser.add_argument(
        'client_cert',
        help='path to file containing client certificate and key (common prod)'
    )
    parser.add_argument(
        'input_dir',
        type=Path,
        help='input directory containing original files'
    )
    parser.add_argument(
        'output_dir',
        type=Path,
        help='output directory for new files'
    )

    return parser.parse_args()


def load_update_list_version(input_dir: Path) -> int:
    path = input_dir / latest_update_list_version_name
    if not path.exists():
        return 1
    return int(path.read_text())


def write_update_list_version(output_dir: Path, version: int) -> None:
    path = output_dir / latest_update_list_version_name
    path.write_text(str(version))


def main() -> None:
    args = parse_args()

    # set up logging
    logging.basicConfig(format='%(asctime)s: [%(levelname)s] %(name)s: %(message)s')
    logging.getLogger('wiiu_database_updater').setLevel(getattr(logging, args.log_level.upper()))
    for name in ('reqcli', 'nus_tools'):
        logging.getLogger(name).setLevel(getattr(logging, args.log_level_dep.upper()))

    # load root publickey for verifying signatures
    if args.root_key_file:
        NUSToolsConfiguration.root_key_struct = rootkey.parse_file(args.root_key_file)

    if args.ignore_last_update_list_version:
        latest_update_list_version = 1
    else:
        latest_update_list_version = load_update_list_version(args.input_dir)

    db = Database(str(args.input_dir))
    db.read_all()

    eshop = EShop(
        db,
        args.client_cert,
        not args.no_reload,
        SourceConfig(requests_per_second=args.requests_per_second)
    )

    if args.get_titles:
        # load titles
        for region in (Region.EUR, Region.USA, Region.JPN, Region.KOR):
            eshop.get_titles(region, args.shop_id)

    if args.get_updates:
        # load updates
        latest_update_list_version = eshop.get_wiiu_updates(latest_update_list_version)

    if args.get_dlcs:
        # load dlcs
        eshop.get_wiiu_dlcs()

    db.fixup_regions()
    db.write_all(str(args.output_dir))

    write_update_list_version(args.output_dir, latest_update_list_version)


main()
