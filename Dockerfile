FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

CMD ["python", "main.py"]
