FROM python:3.9-alpine

ENV PYTHONUNBUFFERED=1
WORKDIR /opt/shadow

RUN apk update && \
    apk add --update git zlib jpeg freetype libwebp libffi openssl && \
    apk add --update --virtual .build-deps git build-base linux-headers zlib-dev jpeg-dev freetype-dev libwebp-dev libffi-dev openssl-dev && \
    rm -rf /root/.cache && \
    apk del .build-deps && \
    apk --no-cache add gcc musl-dev

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "-u", "src/main.py" ]
