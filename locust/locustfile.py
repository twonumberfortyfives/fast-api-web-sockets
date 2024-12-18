import random
import string
from locust import HttpUser, task, between
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


MOCK_DATABASE_URL = (
    "postgresql://mock_agora:mock_password@mock_postgres:5432/mock_postgres"
)

engine = create_engine(MOCK_DATABASE_URL, echo=True)

Session = sessionmaker(bind=engine)


def generate_random_user():
    username = "".join(random.choices(string.ascii_lowercase, k=8))
    email = username + "@example.com"
    password = "passworD123!"
    return {"username": username, "email": email, "password": password}


class UserBehavior(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def register_user(self):
        user_data = generate_random_user()
        response = self.client.post("/api/register", json=user_data)
        if response.status_code == 201:
            print(f"User {user_data['username']} registered successfully.")
        else:
            print(
                f"Registration failed for {user_data['username']}. Status code: {response.status_code}"
            )

    def on_start(self):
        session = Session()
        try:
            session.execute(text("DELETE FROM users"))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error during clearing users: {e}")
        finally:
            session.close()

    def on_stop(self):
        session = Session()
        try:
            session.execute(text("DELETE FROM users"))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error during clearing users: {e}")
        finally:
            session.close()
