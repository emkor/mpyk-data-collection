FROM python:3.9-slim-buster

WORKDIR /mpyk

COPY requirements.txt .
RUN pip install --no-cache-dir  -r ./requirements.txt

RUN mkdir -p /mpyk/csv && mkdir -p /mpyk/zip

COPY mpyk_collect.py .
RUN chmod u+x mpyk_collect.py

CMD ["python", "./mpyk_collect.py", "15", "/mpyk/csv", "/mpyk/zip"]