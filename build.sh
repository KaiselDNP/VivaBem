#!/usr/bin/env bash
set -o errexit

python -m pip install -r requirements/base.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py bootstrap_admin
