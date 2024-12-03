import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("MOCK_DATABASE_URL")
MAIN_PAGE = "http://frontend:5173"
LOGIN_PAGE = "http://frontend:5173/login"
REGISTER_PAGE = "http://frontend:5173/register"
PROFILE_PAGE = "http://frontend:5173/profile"
USERS_PAGE = "http://frontend:5173/users"
