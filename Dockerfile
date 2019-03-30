FROM python:3.7-alpine AS base

WORKDIR /opt/receipt-tracker-build

COPY Pipfile Pipfile.lock /opt/receipt-tracker-build/

RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev python3-dev libxml2-dev && \
    apk add --no-cache postgresql-libs libxslt-dev && \
    pip install pipenv && \
    pipenv lock -r > requirements.txt 2>/dev/null && \
    pipenv lock -r --dev > requirements-dev.txt 2>/dev/null && \
    pip install -r requirements.txt && \
    pipenv --rm && \
    pip uninstall -y pipenv && \
    apk del --no-cache .build-deps

COPY manage.py /opt/receipt-tracker/
#COPY receipt_tracker /opt/receipt-tracker/receipt_tracker

# Prod
FROM python:3.7-alpine AS prod

WORKDIR /opt/receipt-tracker

COPY --from=base /usr/ /usr/
COPY --from=base /opt/receipt-tracker/ /opt/receipt-tracker/

CMD gunicorn -b 0.0.0.0:80 receipt_tracker/wsgi.py

# Dev
FROM python:3.7-alpine AS dev

WORKDIR /opt/receipt-tracker

COPY --from=base /usr/ /usr/
COPY --from=base /opt/receipt-tracker/ /opt/receipt-tracker/
COPY --from=base /opt/receipt-tracker-build/requirements-dev.txt /opt/receipt-tracker/

COPY setup.cfg /opt/receipt-tracker/

RUN pip install -r requirements-dev.txt

CMD pytest --cov
