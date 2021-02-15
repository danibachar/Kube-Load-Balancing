FROM danibachar/kube-dash:latest

ENV DASH_DEBUG_MODE False

RUN pip install mod_wsgi-httpd
RUN pip install mod-wsgi

#RUN pwd
#RUN ls -l bin | grep kubernetes

#COPY ./app/kubernetes_servcice_selection/src/kubernetes_servcice_selection/dev_cli.py ./src/kubernetes_servcice_selection
#COPY ./app/kubernetes_servcice_selection/bin/run-kubernetes_servcice_selection-prod ./bin

#RUN cat ./bin/run-kubernetes_servcice_selection-prod

CMD ["run-kubernetes_servcice_selection-dev"]
