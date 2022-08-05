FROM python:3.10-alpine

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

# gcc is needed to build uvloop
RUN apk add -t requirements_libs --no-cache \
    gcc \
    musl-dev

COPY requirements.txt /requirements.txt

# RUN python -m ensurepip
RUN pip install --upgrade pip setuptools
RUN pip install -r /requirements.txt

RUN apk del requirements_libs

COPY scripts /scripts
RUN chmod u+x /scripts/*

COPY mirror/ /srv/root

EXPOSE 80

WORKDIR /srv/root

CMD ["/scripts/start.sh"]
