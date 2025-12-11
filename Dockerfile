FROM python:3-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache zfs

COPY main.py requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./main.py"]
