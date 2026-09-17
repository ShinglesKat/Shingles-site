# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # load .env file once here

SECRET_KEY = os.getenv('SECRET_KEY')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
DEBUG = os.getenv('FLASK_DEBUG') == '1'
SAVE_INTERVAL = 300

DEFAULT_COLOUR = "#ffffff"
CELL_SIDE_COUNT = 50

FREEVIEW_PAGE = "https://www.matthuisman.nz/2021/02/new-zealand-apks-for-sideloading.html"
FREEVIEW_URL_PREFIX = "https://f.mjh.nz/apk/nz/freeview-atv-unlocked-"
