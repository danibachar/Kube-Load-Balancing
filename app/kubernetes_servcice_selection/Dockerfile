FROM python:3.9

ENV DASH_DEBUG_MODE Talse
COPY ./ /app
WORKDIR /app
RUN set -ex && \
    pip install -r requirements.txt
EXPOSE 8050
CMD ["python", "app.py"]
