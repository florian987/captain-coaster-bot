FROM hub.hsfactory.net/jeff/discord-bot:base

ENV PIPENV_VENV_IN_PROJECT=1
ENV PIPENV_IGNORE_VIRTUALENVS=1
ENV PIPENV_NOSPIN=1
ENV PIPENV_HIDE_EMOJIS=1

RUN pip install pipenv

COPY . /bot
WORKDIR /bot

RUN pipenv sync

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["pipenv", "run", "start"]
