Парсер на Scrapy для сбора каталога товаров с www.ysl.com/en-en и загрузки данных в гугл-таблицу. 

Change ip and port
version: '3'

services:
  selenium:
    image: selenium/standalone-chrome:latest
    ports:
      - "4444:4444"
      - "7900:7900"
    shm_size: 2g
    restart: always

  parser:
    image: telsamar/parser:v4
    restart: always
