FROM docker.catalyst.net.nz/catalyst/ubuntu:22.04 as base

LABEL maintainer="dtta-ams-dev@catalyst.net.nz"

RUN sed -i 's/archive.ubuntu.com/ubuntu.catalyst.net.nz/' /etc/apt/sources.list

RUN apt-get update \
    && apt-get install -qyy -o APT::Install-Recommends=false -o APT::Install-Suggests=false \
    vim \
    less \
    wget \
    binutils \
    build-essential \
    gettext \
    python3-dev \
    python3-venv \
    postgresql-client-common \
    postgresql-client-14 \
    cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV LANG C.UTF-8

ARG DOCKER_USER_UID=999

RUN useradd \
    --create-home \
    --groups users \
    --shell /bin/bash \
    --uid "${DOCKER_USER_UID}" \
    user

WORKDIR /src/app
RUN chown user:users .

USER user

ARG POETRY_VERSION=1.5.1

RUN wget -O install-poetry.py https://install.python-poetry.org \
    && python3 install-poetry.py "--version=${POETRY_VERSION}" --yes \
    && rm install-poetry.py

ENV PATH="/home/user/.local/bin/:${PATH}"

USER root

COPY cronjobs /etc/cron.d/ams
RUN chmod 0644 /etc/cron.d/ams
RUN crontab -u user /etc/cron.d/ams

RUN touch /var/log/cron.log
RUN chown user:users /var/log/cron.log

USER user

ENTRYPOINT ["poetry", "run", "gunicorn", "ams.wsgi:application"]

################
# dev
################
FROM base as dev

################
# production 
################
FROM base as production

USER user

COPY pyproject.toml .
COPY poetry.lock .
COPY poetry.toml .
RUN poetry install

COPY . .