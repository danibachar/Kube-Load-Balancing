FROM python:3.6

ENV DASH_DEBUG_MODE True
COPY ./ ./main.csv
COPY ./dataframes ./dataframes

RUN apt-get update -y && apt-get install python3-dev graphviz libgraphviz-dev pkg-config -y

COPY ./ ./
RUN set -ex && \
    pip install -e .


ENV DATAFRAME_NAME='/main.csv'

RUN pwd
RUN ls

EXPOSE $PORT
CMD ["run-kubernetes_servcice_selection-dev"]
