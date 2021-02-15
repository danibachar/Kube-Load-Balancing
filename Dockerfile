FROM danibachar/kube-dash:latest

RUN pwd
RUN ls

PORT=8050
EXPOSE $PORT
CMD ["run-kubernetes_servcice_selection-dev"]
