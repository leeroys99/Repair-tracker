FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask gunicorn

EXPOSE 5000

CMD ["sh", "-c", "python database.py && exec gunicorn --bind 0.0.0.0:5000 app:app"]
