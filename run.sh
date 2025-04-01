#!/bin/bash
# if you modify models, you need to run this command
python manage.py makemigrations
python manage.py migrate
python manage.py initadmin --username saferman --password 0esilent4
python manage.py runserver 0.0.0.0:5000 --noreload
