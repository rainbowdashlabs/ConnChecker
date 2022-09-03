FROM python:3.10

WORKDIR app/

RUN pip install --upgrade pip && pip install pipenv

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --system

COPY src/ .

COPY config/logging.yml logging.yml

ENTRYPOINT ["python", "main.py"]