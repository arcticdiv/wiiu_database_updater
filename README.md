# wiiu_database_updater
This tool updates the .json database files used by Wii U USB Helper.    
<sub>* This program is not needed for normal operation of Wii U USB Helper, it's intended for development purposes</sub>

---

## Install
Requires Python `>= 3.7`
```
pip install git+https://github.com/arcticdiv/wiiu_database_updater
```

## Usage
Refer to the [nus_tools README](https://github.com/arcticdiv/nus_tools/blob/master/README.md) for more info on certificates/keys.

```
usage: wiiu_database_updater [-h] [-l LOG_LEVEL] [-ld LOG_LEVEL_DEP] [--root-key-file ROOT_KEY_FILE]
                             [--cache-file CACHE_FILE] [--ignore-last-update-list-version] [-n]
                             [--shop-id {1,2,3,4}] [-r REQUESTS_PER_SECOND] [--no-titles]
                             [--no-updates] [--no-dlcs]
                             client_cert input_dir output_dir

positional arguments:
  client_cert           path to file containing client certificate/key bundle (common prod)
  input_dir             input directory containing original files
  output_dir            output directory for new files

optional arguments:
  -h, --help            show this help message and exit
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        logging level (valid values are python's builtin logging levels) (default: INFO)
  -ld LOG_LEVEL_DEP, --log-level-dep LOG_LEVEL_DEP
                        logging level for dependendencies (default: INFO)
  --root-key-file ROOT_KEY_FILE
                        path to 'Root' public key (signing CA for TMD/Ticket files) (default: None)
  --cache-file CACHE_FILE
                        request database cache path (default: ./requests_cache.db)
  --ignore-last-update-list-version
                        ignore any stored update list version files, always start from 1 (default: False)
  -n, --no-reload       enable reading most responses from cache (useful for debugging) (default: False)
  --shop-id {1,2,3,4}   shop ID used for retrieving new titles (default: 2)
  -r REQUESTS_PER_SECOND, --ratelimit REQUESTS_PER_SECOND
                        maximum requests per host per second (default: 2)
  --no-titles           don't retrieve new titles (default: True)
  --no-updates          don't retrieve new updates (default: True)
  --no-dlcs             don't retrieve new dlcs (default: True)
```

## Docker
The docker image (see [`Dockerfile`](./Dockerfile)) can be used with the following command:

```shell
$ docker run --rm -v $(pwd)/data:/app/data \
    arcticdiv/wiiu_database_updater \
    `#optional` \
    --root-key-file data/root-key \
    [additional args]
```
When building the image yourself, note the special [`Dockerfile.armv7`](./Dockerfile.armv7) for, you guessed it, armv7 architectures, since those (currently) need to build `lxml` from source.

The `./data` directory should be set up to look like this:
```
|- orig
|  |- customs.json
|  |- ...
|
|- new
|  |- [updated files will be put here]
|
|- WIIU_COMMON_1_CERT.pem
|- root-key (optional)
```
