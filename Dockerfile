FROM python:3.12-slim
LABEL maintainer="admin@admin.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /files/media

RUN adduser \
    --disabled-password \
    --no-create-home \
    theatre_user

RUN chown -R theatre_user /files/media
RUN chmod -R 755 /files/media

USER theatre_user
