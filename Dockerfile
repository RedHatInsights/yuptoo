FROM registry.redhat.io/rhel8/python-39

COPY Pipfile Pipfile.lock main.py ${APP_ROOT}/src/
COPY yuptoo ${APP_ROOT}/src/yuptoo/
RUN pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --system --deploy --ignore-pipfile