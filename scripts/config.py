# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # load .env file once here

SECRET_KEY = os.getenv('SECRET_KEY')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
JWT_EXPIRATION_SECONDS = int(os.getenv('JWT_EXPIRATION_SECONDS', 3600))
SAVE_INTERVAL = 300
CELL_SIDE_COUNT = 50
DEFAULT_COLOUR = "#ffffff"