FROM python:3.6

ENV DASH_DEBUG_MODE True
COPY ./app ./app/kubernetes_servcice_selection/main.csv
COPY ./app ./app/kubernetes_servcice_selection/src
COPY ./app ./app/kubernetes_servcice_selection/bin
COPY ./app ./app/kubernetes_servcice_selection/setup.py


WORKDIR ./app

RUN set -ex && \
    pip install -e .

ENV DATAFRAME_NAME='/main.csv'

RUN pwd
RUN ls

EXPOSE 5000
CMD ["run-kubernetes_servcice_selection-dev"]
