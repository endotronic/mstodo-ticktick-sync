FROM docker.io/library/python:3.9.7-alpine as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS python-deps

# Install pipenv and compilation dependencies
RUN apk add --no-cache build-base
RUN pip install pipenv

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

ARG UID=1012
ARG GID=1012
ARG module_name

RUN addgroup -S -g $GID $module_name
RUN adduser  -S -g $GID -u $UID -h /opt/$module_name $module_name

USER $UID
WORKDIR /opt/$module_name

# Install application into container
COPY $module_name.py .
COPY pymstodo/pymstodo ./pymstodo/

# Run the application
ENV MAIN=$module_name
ENTRYPOINT ["sh", "-c", "python -u $MAIN.py"]