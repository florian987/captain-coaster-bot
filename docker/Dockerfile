FROM python:3.8

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

#RUN pip install pipenv

#COPY Pipfile Pipfile.lock /bot/
COPY requirements.txt /bot/

WORKDIR /bot

#RUN pipenv install --system
#RUN pipenv install --deploy --system --ignore-pipfile
RUN pip install -r requirements.txt

COPY . /bot

CMD ["python", "-m", "bot"]
