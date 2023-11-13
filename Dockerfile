FROM python:3.11-alpine AS poetry

RUN apk update && apk upgrade && \
    apk add curl gcc python3-dev libc-dev build-base linux-headers && \
    rm -rf /var/cache/apk
RUN curl https://install.python-poetry.org | python -

COPY pyproject.toml /opt/SportTracker/pyproject.toml
COPY poetry.lock /opt/SportTracker/poetry.lock

WORKDIR /opt/SportTracker
RUN /root/.local/bin/poetry install --no-root
RUN ln -s $($HOME/.local/share/pypoetry/venv/bin/poetry env info -p) /opt/SportTracker/myvenv

FROM python:3.11-alpine

RUN apk update && apk upgrade && \
    apk add git && \
    rm -rf /var/cache/apk

COPY src/ /opt/SportTracker/src
COPY --from=poetry /opt/SportTracker/myvenv /opt/SportTracker/myvenv

RUN adduser -D sportracker && chown -R sportracker /opt/SportTracker
USER sportracker

WORKDIR /opt/SportTracker/src
EXPOSE 8080
CMD [ "/opt/SportTracker/myvenv/bin/python", "/opt/SportTracker/src/SportTracker.py"]
