FROM registry.access.redhat.com/ubi9/s2i-base:9.7-1768264882 AS kafka_build
USER 0
ADD librdkafka .
RUN ./configure --prefix=/usr && \
    make && \
    make install

FROM registry.access.redhat.com/ubi9/ubi-minimal:9.7-1768783948


# Install dependencies, including runtime libraries
RUN microdnf install --setopt=tsflags=nodocs -y python3.11 python3.11-pip python3.11-devel which gcc gcc-c++ make zlib zlib-devel openssl-libs openssl-devel libzstd libzstd-devel zip && \
    microdnf upgrade -y && \
    microdnf clean all

ENV APP_ROOT=/opt/app-root
WORKDIR $APP_ROOT/src/

RUN set -ex && if [ -e `which python3.11` ]; then ln -s `which python3.11` /usr/local/bin/python; fi

# install librdkafka
COPY --from=kafka_build /usr/lib/librdkafka*.so* /usr/lib/
COPY --from=kafka_build /usr/lib/pkgconfig/rdkafka*.pc /usr/lib/pkgconfig/
COPY --from=kafka_build /usr/include/librdkafka /usr/include/librdkafka
RUN ldconfig

COPY Pipfile Pipfile.lock main.py ${APP_ROOT}/src/
RUN python -m pip install --upgrade pip && \
    python -m pip install pipenv --ignore-installed && \
    pipenv install --system --ignore-pipfile
COPY yuptoo ${APP_ROOT}/src/yuptoo/

RUN microdnf remove -y which gcc gcc-c++ make zlib-devel openssl-devel libzstd-devel zip && \
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
