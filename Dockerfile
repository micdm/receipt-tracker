FROM python:3.7 AS base

WORKDIR /opt/receipt-tracker-build

COPY Pipfile Pipfile.lock /opt/receipt-tracker-build/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt 2>/dev/null && \
    pipenv lock -r --dev > requirements-dev.txt 2>/dev/null && \
    pip install -r requirements.txt && \
    pipenv --rm && \
    pip uninstall -y pipenv

COPY manage.py /opt/receipt-tracker/
COPY receipt_tracker /opt/receipt-tracker/receipt_tracker

# Prod
FROM python:3.7 AS prod

WORKDIR /opt/receipt-tracker

COPY --from=base /usr/ /usr/
COPY --from=base /opt/receipt-tracker/ /opt/receipt-tracker/

CMD ["gunicorn", "-c", "/etc/gunicorn.conf", "receipt_tracker.wsgi:application"]

# Dev
FROM python:3.7 AS dev

WORKDIR /opt/receipt-tracker

COPY --from=base /usr/ /usr/
COPY --from=base /opt/receipt-tracker/ /opt/receipt-tracker/
COPY --from=base /opt/receipt-tracker-build/requirements-dev.txt /opt/receipt-tracker/

COPY setup.cfg /opt/receipt-tracker/

RUN pip install -r requirements-dev.txt

CMD ["pytest", "--cov"]
