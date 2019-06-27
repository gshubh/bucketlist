# Dockerfile - this is a comment. Delete me if you want.
FROM python:2.7

COPY . /app

WORKDIR /app

ENV APP_SETTINGS="development"

ENV FLASK_APP="run.py"

ENV SECRET="BNYRKQGHEVM;TGO'LB'P[\BLYLPBOP,P"

ENV DATABASE_URL="postgresql://postgres:siemens@172.17.0.1:54321/flask_api"

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["run.py"]