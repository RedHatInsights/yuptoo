FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

RUN microdnf install --setopt=tsflags=nodocs -y python3.11 python3.11-pip which && \
    microdnf upgrade -y && \
    microdnf clean all

ENV APP_ROOT=/opt/app-root
WORKDIR $APP_ROOT/src/

RUN set -ex && if [ -e `which python3.11` ]; then ln -s `which python3.11` /usr/local/bin/python; fi

COPY Pipfile Pipfile.lock main.py ${APP_ROOT}/src/
RUN python -m pip install --upgrade pip && \
    python -m pip install pipenv && \
    pipenv install --system --ignore-pipfile
COPY yuptoo ${APP_ROOT}/src/yuptoo/
