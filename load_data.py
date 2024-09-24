import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import DBUser, DBPost

from dotenv import load_dotenv


load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
db = Session()


def load_extended_sample_data(json_file: str):
    db.query(DBPost).delete()
    db.query(DBUser).delete()
    db.commit()

    with open(json_file, "r") as f:
        data = json.load(f)

    for user_data in data["users"]:
        user = DBUser(
            id=user_data["id"],
            email=user_data["email"],
            username=user_data["username"],
            password=user_data["password"],
            role=user_data["role"],
        )
        db.add(user)
        for post_data in user_data["posts"]:
            post = DBPost(
                id=post_data["id"],
                topic=post_data["topic"],
                content=post_data["content"],
                user_id=user.id,
            )
            db.add(post)

    db.commit()


if __name__ == "__main__":
    load_extended_sample_data("test_data.json")
