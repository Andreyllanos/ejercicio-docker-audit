FROM python:3.8
WORKDIR /app

COPY . /app

RUN pip install Flask==1.1.2 PyMySQL==0.9.3 Jinja2==2.11.3 MarkupSafe==1.1.1 itsdangerous==2.0.1

EXPOSE 5050
CMD ["python", "app.py"]