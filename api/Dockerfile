#           BASIC FILE SETUP

FROM        python:3.11-slim-bullseye AS base

LABEL       author="Isaac Kogan" maintainer="info@isaackogan.com"

ARG USER="sign-wss"
ARG USER_ID="1000"
ARG PYTHON="python3"

RUN apt-get update \
 && apt-get -y install git gcc g++ ca-certificates dnsutils curl iproute2 ffmpeg procps tini libmagic1 \
 && useradd -m -d /home/${USER} ${USER}

FROM base AS with_packages
# ENV CONFIGURATION

ENV USER="${USER}"
ENV HOME="/home/${USER}"
ENV PIP="${PYTHON} -m pip"

# USER CONFIGURATION

USER ${USER}
WORKDIR /home/${USER}

# INSTALL PYTHON DEPENDENCIES

COPY requirements.txt ./
RUN ${PIP} install -r ./requirements.txt && rm ./requirements.txt

# With packages

FROM with_packages AS final

# PROJECT SOURCE CODE

COPY ./app ./app

# START SERVER

COPY --chown=${USER}:${USER} ./entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["/entrypoint.sh", "sign-wss"]
