FROM python:3.14.7-alpine3.24@sha256:05b2b8b732ecd268fee8727a369f936f022d1321b59befd13c30ede22769dcdc

RUN addgroup -g 10001 -S plugin && adduser -u 10001 -S -G plugin plugin

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY --chown=plugin:plugin app /app/app

USER 10001:10001
ENTRYPOINT ["python3", "-m", "app.main"]
