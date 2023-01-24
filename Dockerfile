FROM registry.access.redhat.com/ubi8/ubi-minimal:latest

RUN microdnf module enable python39:3.9 && \
    microdnf install --setopt=tsflags=nodocs -y python39 && \
    microdnf upgrade -y && \
    microdnf clean all

ENV APP_ROOT=/opt/app-root
WORKDIR $APP_ROOT/src/

COPY Pipfile Pipfile.lock main.py ${APP_ROOT}/src/
RUN python -m pip install --upgrade pip && \
    python -m pip install pipenv && \
    pipenv install --system --ignore-pipfile
COPY yuptoo ${APP_ROOT}/src/yuptoo/
