FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python -
COPY . /opt/SportTracker
RUN rm /opt/SportTracker/settings.json

WORKDIR /opt/SportTracker
RUN /root/.local/bin/poetry install --no-root && \
    /root/.local/bin/poetry cache clear --all .
RUN ln -s $($HOME/.local/share/pypoetry/venv/bin/poetry env info -p) /opt/SportTracker/myvenv

WORKDIR /opt/SportTracker/src
CMD [ "/opt/SportTracker/myvenv/bin/python", "/opt/SportTracker/src/SportTracker.py"]
