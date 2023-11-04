# Используйте образ Node.js для установки зависимостей и сборки статических файлов
FROM node:14 as build-stage

WORKDIR /app

# Копируем файлы, необходимые для сборки статических файлов
COPY ./bundles-src /app/bundles-src
COPY ./package.json ./package-lock.json /app/

# Установка зависимостей Node.js и сборка статических файлов
RUN npm ci --also=dev
RUN npm run build

FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY --from=build-stage /app/bundles /app/static
COPY requirements.txt /app/

RUN pip install --upgrade pip --default-timeout=100 && \
    pip install -r requirements.txt --default-timeout=100

# Установка зависимостей для psycopg2
RUN apt-get update && \
    apt-get install -y libpq-dev gcc && \
    pip install psycopg2


COPY . /app/


EXPOSE 8000

CMD ["gunicorn", "star_burger.wsgi:application", "--bind", "0.0.0.0:8000"]
