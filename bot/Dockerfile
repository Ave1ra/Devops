FROM python:3.10-alpine
WORKDIR /bot
COPY . .
RUN apk update \
    && apk add libpq postgresql-dev \
    && apk add build-base
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 1313

CMD ["python", "bot.py"]
