import os

from dotenv import load_dotenv, find_dotenv

# Load environment variables from a .env file if it exists
load_dotenv(find_dotenv())

BASE_SERVER_URL = os.getenv("BASE_SERVER_URL")
