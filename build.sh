#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
flask db upgrade
python create_admin.py
python init_subscription_plans.py
python import_if_empty.py
