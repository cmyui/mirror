FROM python:3.10

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

COPY requirements.txt /requirements.txt

# RUN python -m ensurepip
RUN pip install --upgrade pip setuptools
RUN pip install -r /requirements.txt

COPY scripts /scripts
RUN chmod u+x /scripts/*

COPY mirror/ /srv/root

EXPOSE 80

WORKDIR /srv/root

CMD ["/scripts/start.sh"]
