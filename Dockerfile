FROM danibachar/kube-dash:latest

#ENV DASH_DEBUG_MODE True

#RUN pip install mod_wsgi-httpd
#RUN pip install mod-wsgi

#RUN pwd

#COPY ./app/kubernetes_servcice_selection/bin/run-kubernetes_servcice_selection-prod ./bin
#COPY ./app/kubernetes_servcice_selection ./
#COPY ./app/kubernetes_servcice_selection/src/kubernetes_servcice_selection/dev_cli.py ./src/kubernetes_servcice_selection/
COPY ./app/kubernetes_servcice_selection ./
RUN ls -l ./
RUN cat ./src/kubernetes_servcice_selection/dev_cli.py
RUN cat ./src/kubernetes_servcice_selection/utils.py

EXPOSE $PORT
CMD ["run-kubernetes_servcice_selection-dev"]
