FROM registry.redhat.io/rhel8/python-39

COPY Pipfile Pipfile.lock main.py ${APP_ROOT}/src/
RUN pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --system --ignore-pipfile
COPY yuptoo ${APP_ROOT}/src/yuptoo/
