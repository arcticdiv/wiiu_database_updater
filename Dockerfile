FROM python:3-alpine


WORKDIR /app
COPY setup.py requirements.txt ./
RUN apk add --no-cache --update --virtual build-dependencies build-base python3-dev libxslt-dev git \
 && apk add --no-cache libxslt \
 && mkdir wiiu_database_updater \
 && pip install -e . \
 && apk del build-dependencies

COPY . .

VOLUME ./data

ENTRYPOINT [ \
    "python", "-m", "wiiu_database_updater", \
    "data/WIIU_COMMON_1_CERT.pem", "data/orig", "data/new", \
    "--cache-file", "data/requests_cache.db" \
]
