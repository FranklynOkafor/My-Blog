FROM python

EXPOSE 5000

ADD requirements.txt .

RUN python3 -m pip install -r requirements.txt

WORKDIR /app

ADD . /app

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "blog_app.webapp:app"]