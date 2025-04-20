FROM python:3.11
COPY . /app
WORKDIR /app
VOLUME /app/static
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["main.py"]