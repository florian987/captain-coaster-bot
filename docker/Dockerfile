FROM python:3.6-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    zlib1g \
    libxml2 libxml2-dev libxslt1-dev \
    freetype2-demos libfreetype6 libfreetype6-dev \
    opus-tools \
    ffmpeg \
    chromium \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv

ENV LIBRARY_PATH=/lib:/usr/lib \
    PIPENV_VENV_IN_PROJECT=1 \
    PIPENV_IGNORE_VIRTUALENVS=1 \
    PIPENV_NOSPIN=1 \
    PIPENV_HIDE_EMOJIS=1

COPY Pipfile Pipfile.lock /bot/

WORKDIR /bot

RUN pipenv install --deploy --system --ignore-pipfile

COPY . /bot

CMD ["python", "-m", "bot"]
