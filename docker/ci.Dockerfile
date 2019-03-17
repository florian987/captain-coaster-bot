FROM python:3.6-slim-stretch

RUN apt update && apt -y install \
    libffi-dev

# RUN apk add --update docker \
#                      curl \
#                      tini \
#                      build-base \
#                      libffi-dev \
#                      zlib \
#                      jpeg-dev \
#                      libxml2 libxml2-dev libxslt-dev \
#                      zlib-dev \
#                      freetype-dev \
#                      git

RUN pip install --upgrade pip && pip install pipenv

ENV LIBRARY_PATH=/lib:/usr/lib
ENV PIPENV_VENV_IN_PROJECT=1
ENV PIPENV_IGNORE_VIRTUALENVS=1
ENV PIPENV_NOSPIN=1
ENV PIPENV_HIDE_EMOJIS=1
