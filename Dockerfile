FROM python:3.14-slim AS poetry

RUN apt-get update && apt-get install -y \
    curl gcc python3-dev libc-dev build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl https://install.python-poetry.org | python -

COPY pyproject.toml /opt/SportTracker/pyproject.toml
COPY poetry.lock /opt/SportTracker/poetry.lock
COPY sporttracker/ /opt/SportTracker/sporttracker

WORKDIR /opt/SportTracker
RUN /root/.local/bin/poetry install --without dev
RUN ln -s $($HOME/.local/share/pypoetry/venv/bin/poetry env info -p) /opt/SportTracker/myvenv


FROM node:26-slim AS npm

RUN apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

COPY js/ /opt/SportTracker/js
RUN mkdir -p /opt/SportTracker/sporttracker/static/js/libs

WORKDIR /opt/SportTracker/js

RUN npm ci && npm run build


FROM python:3.14-slim

RUN apt-get update && apt-get install -y \
    libpq5 libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY sporttracker/ /opt/SportTracker/sporttracker
COPY CHANGES.md /opt/SportTracker/CHANGES.md
COPY --from=poetry /opt/SportTracker/myvenv /opt/SportTracker/myvenv
COPY --from=npm /opt/SportTracker/sporttracker/static/js/libs/libs.js /opt/SportTracker/sporttracker/static/js/libs/libs.js
COPY --from=npm /opt/SportTracker/sporttracker/static/js/libs/libs.css /opt/SportTracker/sporttracker/static/js/libs/libs.css
COPY --from=npm /opt/SportTracker/sporttracker/static/js/libs/plotly.js /opt/SportTracker/sporttracker/static/js/libs/plotly.js
COPY --from=npm /opt/SportTracker/sporttracker/static/js/libs/leaflet.js /opt/SportTracker/sporttracker/static/js/libs/leaflet.js

RUN adduser sporttracker && chown -R sporttracker:sporttracker /opt/SportTracker
USER sporttracker

WORKDIR /opt/SportTracker/sporttracker
EXPOSE 8080
CMD [ "/opt/SportTracker/myvenv/bin/python", "/opt/SportTracker/sporttracker/SportTracker.py"]