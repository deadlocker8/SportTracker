FROM python:3.12-alpine AS poetry

RUN apk update && apk upgrade && \
    apk add curl gcc python3-dev libc-dev build-base linux-headers postgresql-dev && \
    rm -rf /var/cache/apk
RUN curl https://install.python-poetry.org | python -

COPY pyproject.toml /opt/SportTracker/pyproject.toml
COPY poetry.lock /opt/SportTracker/poetry.lock
COPY sporttracker/ /opt/SportTracker/sporttracker

WORKDIR /opt/SportTracker
RUN /root/.local/bin/poetry install --without dev
RUN ln -s $($HOME/.local/share/pypoetry/venv/bin/poetry env info -p) /opt/SportTracker/myvenv

FROM node:23-alpine AS npm

RUN apk update && apk upgrade && \
    rm -rf /var/cache/apk

COPY js/ /opt/SportTracker/js
RUN mkdir -p /opt/SportTracker/sporttracker/static/js/libs

WORKDIR /opt/SportTracker/js

RUN npm ci && npm run build

FROM python:3.12-alpine

RUN apk update && apk upgrade && \
    apk add postgresql-libs && \
    rm -rf /var/cache/apk

COPY sporttracker/ /opt/SportTracker/sporttracker
COPY CHANGES.md /opt/SportTracker/CHANGES.md
COPY --from=poetry /opt/SportTracker/myvenv /opt/SportTracker/myvenv
COPY --from=npm /opt/SportTracker/sporttracker/static/js/libs/main.css /opt/SportTracker/sporttracker/static/js/libs/main.css
COPY --from=npm /opt/SportTracker/sporttracker/static/js/libs/libs.js /opt/SportTracker/sporttracker/static/js/libs/libs.js

RUN adduser -D sporttracker && chown -R sporttracker:sporttracker /opt/SportTracker
USER sporttracker

WORKDIR /opt/SportTracker/sporttracker
EXPOSE 8080
CMD [ "/opt/SportTracker/myvenv/bin/python", "/opt/SportTracker/sporttracker/SportTracker.py"]
