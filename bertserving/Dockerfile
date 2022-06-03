FROM tensorflow/tensorflow:1.12.0-py3
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install --no-cache-dir bert-serving-server==1.10.0
COPY entrypoint.sh /app
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]