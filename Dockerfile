FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install-deps \
    && playwright install

CMD ["python", "main.py"]