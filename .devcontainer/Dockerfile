FROM mcr.microsoft.com/devcontainers/python:3.12

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

ADD .devcontainer/dev-requirements.txt /tmp/dev-requirements.txt
RUN pip install -r /tmp/dev-requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/workspaces/data_config/"