FROM python:3.12-alpine3.22@sha256:a190708a2dec1bd18b1decb539f8e8f5407abaa9bf39cacda583f7f8c11db322

RUN addgroup -g 10001 -S plugin && adduser -u 10001 -S -G plugin plugin

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY --chown=plugin:plugin app /app/app

USER 10001:10001
ENTRYPOINT ["python3", "-m", "app.main"]
