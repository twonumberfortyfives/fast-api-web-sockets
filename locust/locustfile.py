import random
import string
from locust import HttpUser, task, between
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Define the synchronous database URL
MOCK_DATABASE_URL = "postgresql://mock_agora:mock_password@mock_postgres:5432/mock_postgres"

# Create a synchronous engine
engine = create_engine(MOCK_DATABASE_URL, echo=True)

Session = sessionmaker(bind=engine)


def generate_random_user():
    username = ''.join(random.choices(string.ascii_lowercase, k=8))  # Random username
    email = username + "@example.com"  # Random email based on username
    password = "passworD123!"  # Hardcoded password (you can modify this)
    return {"username": username, "email": email, "password": password}


class UserBehavior(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def register_user(self):
        user_data = generate_random_user()  # Generate random user data
        response = self.client.post("/api/register", json=user_data)  # POST request to register
        if response.status_code == 201:  # Success status code for creation
            print(f"User {user_data['username']} registered successfully.")
        else:
            print(f"Registration failed for {user_data['username']}. Status code: {response.status_code}")

    def on_start(self):
        """Clear the users table before each test."""
        session = Session()  # Create a synchronous session
        try:
            # Delete all users from the 'users' table
            session.execute(text("DELETE FROM users"))
            session.commit()  # Commit the transaction
        except Exception as e:
            session.rollback()  # Rollback in case of any errors
            print(f"Error during clearing users: {e}")
        finally:
            session.close()  # Close the session

    def on_stop(self):
        """Clear the users table after each test."""
        session = Session()
        try:
            # Delete all users from the 'users' table
            session.execute(text("DELETE FROM users"))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error during clearing users: {e}")
        finally:
            session.close()
