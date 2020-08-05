import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
# SQLALCHEMY_DATABASE_URI = 'postgres:///fyyur'
SQLALCHEMY_DATABASE_URI = 'postgres://uaeumabjvgfwmp:eb5aaf33b22f793a2e2c3d9407559b36d2dfda727ca07f7ee13bbfe29b0f7199@ec2-34-237-89-96.compute-1.amazonaws.com:5432/devk88beeoc2kt'

