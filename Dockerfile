FROM registry.access.redhat.com/ubi9/ubi-minimal:9.7-1764794109


# Install dependencies, including runtime libraries
RUN microdnf install --setopt=tsflags=nodocs -y python3.11 python3.11-pip python3.11-devel which gcc gcc-c++ make zlib zlib-devel openssl-libs openssl-devel cyrus-sasl cyrus-sasl-devel libzstd libzstd-devel zip && \
    microdnf upgrade -y && \
    microdnf clean all

ENV APP_ROOT=/opt/app-root
WORKDIR $APP_ROOT/src/

RUN set -ex && if [ -e `which python3.11` ]; then ln -s `which python3.11` /usr/local/bin/python; fi

# Download and install librdkafka
RUN curl -L https://github.com/confluentinc/librdkafka/archive/refs/tags/v2.12.0.zip -o /tmp/librdkafka.zip || cp /cachi2/output/deps/generic/v2.12.0.zip /tmp/librdkafka.zip && \
    unzip /tmp/librdkafka.zip -d /tmp && \
    cd /tmp/librdkafka-2.12.0 && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    ldconfig && \
    rm -rf /tmp/librdkafka*

COPY Pipfile Pipfile.lock main.py ${APP_ROOT}/src/
RUN python -m pip install --upgrade pip && \
    python -m pip install pipenv --ignore-installed && \
    pipenv install --system --ignore-pipfile
COPY yuptoo ${APP_ROOT}/src/yuptoo/

RUN microdnf remove -y which gcc gcc-c++ make zlib-devel openssl-devel cyrus-sasl cyrus-sasl-devel libzstd-devel zip && \
    microdnf clean all

ENV LD_LIBRARY_PATH=/usr/lib64:/usr/lib

RUN mkdir -p /licenses
COPY LICENSE /licenses

USER 1001

# Define labels for the yuptoo
LABEL url="https://www.redhat.com"
LABEL name="yuptoo" \
      description="This adds the satellite/yuptoo-rhel9 image to the Red Hat container registry. To pull this container image, run the following command: podman pull registry.stage.redhat.io/satellite/yuptoo-rhel9" \
      summary="A new satellite/yuptoo-rhel9 container image is now available as a Technology Preview in the Red Hat container registry."
LABEL com.redhat.component="yuptoo" \
      io.k8s.display-name="IoP Yuptoo" \
      io.k8s.description="This adds the satellite/yuptoo image to the Red Hat container registry. To pull this container image, run the following command: podman pull registry.stage.redhat.io/satellite/yuptoo-rhel9" \
      io.openshift.tags="insights satellite iop yuptoo"
