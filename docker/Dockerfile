FROM hub.hsfactory.net/jeff/discord-bot:base

ENV PIPENV_VENV_IN_PROJECT=1
ENV PIPENV_IGNORE_VIRTUALENVS=1
ENV PIPENV_NOSPIN=1
ENV PIPENV_HIDE_EMOJIS=1
#ENV PATH /bot/scrapper:${PATH}

# RUN pip install pipenv

COPY . /bot
WORKDIR /bot

RUN pipenv install --deploy --system
# RUN pipenv sync

ENTRYPOINT ["/sbin/tini", "--"]
#CMD ["pipenv", "run", "start"]
CMD ["python", "-m", "bot"]
# CMD ["pipenv", "run", "python", "-m", "bot"]
