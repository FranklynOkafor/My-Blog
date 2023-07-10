FROM python

EXPOSE 8080

ADD requirements.txt .

RUN python3 -m pip install -r requirements.txt

WORKDIR /app

ADD . /app

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "blog_app.webapp:app"]