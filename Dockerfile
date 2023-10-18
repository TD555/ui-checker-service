FROM python:3.7.10

RUN apt-get update && \
    apt-get install ffmpeg libsm6 libxext6 -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-login service-ui-checker
USER service-ui-checker

WORKDIR /var/www/ui-checker/ui-checker-service 

COPY --chown=service-ui-checker:service-ui-checker .   /var/www/ui-checker/ui-checker-service 

COPY --chown=service-ui-checker:service-ui-checker ./requirements.txt  /var/www/ui-checker/ui-checker-service/requirements.txt

RUN python3 -m pip install -r requirements.txt

COPY --chown=service-ui-checker:service-ui-checker entrypoint.sh /var/www/ui-checker/ui-checker-service/entrypoint.sh

RUN chmod +x /var/www/ui-checker/ui-checker-service/entrypoint.sh

CMD ["/var/www/ui-checker/ui-checker-service/entrypoint.sh"]
