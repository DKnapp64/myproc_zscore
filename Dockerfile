# syntax = docker/dockerfile:1.0-experimental
FROM ubuntu:18.04

RUN apt update && \
    apt install -y software-properties-common && \
    apt-add-repository ppa:ubuntugis/ppa && \
    apt-add-repository ppa:deadsnakes/ppa && \
    apt update && \
    apt install -y \
    gdal-bin \
    libgdal-dev \
    python3.8 \
    python3.8-dev \
    python3-pip

RUN pip3 install pipenv

WORKDIR /app
COPY . .

# Ref https://click.palletsprojects.com/en/7.x/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN --mount=type=secret,id=pypi_repository_password \
    export PYPI_REPOSITORY_PASSWORD="$(cat /run/secrets/pypi_repository_password)" && \
    pipenv install --dev --sequential

ENV PATH=/app:${PATH}
ENV PYTHONPATH=/app
