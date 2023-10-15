# Используем официальный образ Python
FROM python:3.9-slim-buster

# Устанавливаем необходимые Python-библиотеки
COPY requirements.txt /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/ysl_parser
CMD ["scrapy", "crawl", "ysl"]
