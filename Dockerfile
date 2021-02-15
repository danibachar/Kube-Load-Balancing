FROM danibachar/kube-dash:latest



RUN pwd
RUN ls

EXPOSE 8050
CMD ["run-kubernetes_servcice_selection-dev"]
