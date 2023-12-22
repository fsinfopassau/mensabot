FROM python:3.11

WORKDIR /opt/mensabot
COPY . .

RUN apt update && apt --yes install git && apt clean && \
    pip install --no-cache-dir -r requirements.txt && \
    python setup.py install

VOLUME [ "/data" ]
WORKDIR /data
CMD [ "mensabot" ]
