FROM python:3-slim


RUN apt-get update \
 && apt-get install -y git \
 && apt-get clean \
 && find /var/lib/apt/lists/ /tmp/ /var/tmp/ -mindepth 1 -maxdepth 1 -exec rm -rf "{}" +

WORKDIR /app
COPY setup.py requirements.txt ./
RUN mkdir wiiu_database_updater \
 && pip install -e .

COPY . .

VOLUME ./data

ENTRYPOINT [ \
    "python", "-m", "wiiu_database_updater", \
    "data/WIIU_COMMON_1_CERT.pem", "data/orig", "data/new", \
    "--cache-file", "data/requests_cache.db" \
]
