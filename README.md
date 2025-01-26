# DRF-sample-API
<p>
this is a simple API base on 
<strong><em> Django </em></strong> and
<strong><em> DRF </em></strong>.
</p>
<p>
this API built top of default ViewSet and Router, and have token authorization.
there is diffrent api for admins control and users articles.<br>
there is refresh and login, base on token.<br>
schema base on 
<strong><em> swagger-ui </em></strong> and 
<strong><em> drf-spectacular </em></strong>
</p>

## API Schema

> Path -> /swagger-ui/

![swagger-ui-screenshots](/screenshots/Screenshot%20From%202025-01-26%2014-17-32.png)

## Usage

<p>

we start our python environment

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

after that we run collectstatic and migrate command on database

```
python manage.py migrate
python manage.py collectstatic
```

and running server

```
# with daphne
daphne core.asgi:application

# with django
python manage.py runserver
```

for unit-test

```
python manage.py test
```

</p>

## Built In

<p>

- python-3.13
- django-5.1
- djangorestframework-3.15
- drf-spectacular-0.28
- drf-spectacular-sidecar-2024.12
- daphne-4.1
</p>