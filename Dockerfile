FROM python:3.8-slim-buster

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PORT 5000
ENV USERNAME admin
ENV PASSWORD admin
ENV OPENSSL_CONF /etc/ssl/

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    chrpath \
    libssl-dev \
    libxft-dev \
    libfreetype6 \
    libfreetype6-dev \
    libfontconfig1 \
    libfontconfig1-dev \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r requirements.txt \
    && pip install --upgrade --no-cache-dir git+https://github.com/rongardF/tvdatafeed.git \
    && pip cache purge \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.5.0-beta-linux-ubuntu-xenial-x86_64.tar.gz -O /tmp/phantomjs.tar.gz \
    && tar -xzvf /tmp/phantomjs.tar.gz -C /usr/local/bin \
    && rm /tmp/phantomjs.tar.gz

COPY . /appdocker

RUN chmod +x run.sh

EXPOSE $PORT

CMD /bin/bash