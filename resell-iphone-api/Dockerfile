FROM python:3.11-slim-bullseye
COPY . /app
WORKDIR /app
VOLUME /app/static
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY .env /app/.env  
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015"]