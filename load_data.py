import json
from db.engine import async_session
from db.models import DBUser, DBPost


async def load_extended_sample_data(test_users_data: str, test_posts_data: str):
    async with async_session() as session:
        async with session.begin():
            # Clear existing data
            await session.execute(DBUser.__table__.delete())
            await session.execute(DBPost.__table__.delete())

        # Load users
        with open(test_users_data, "r") as f:
            users_data = json.load(f)

            async with session.begin():
                for user_data in users_data["users"]:  # Adjust for the correct key
                    user = DBUser(
                        id=user_data["id"],
                        email=user_data["email"],
                        username=user_data["username"],
                        password=user_data["password"],
                        profile_picture=user_data["profile_picture"],
                        role=user_data["role"],
                        bio=user_data["bio"],
                    )
                    session.add(user)

        # Load posts
        with open(test_posts_data, "r") as f:
            posts_data = json.load(f)

            async with session.begin():
                for post_data in posts_data["posts"]:  # Adjust for the correct key
                    post = DBPost(
                        topic=post_data["topic"],
                        content=post_data["content"],
                        user_id=post_data["user_id"],
                        _tags=post_data["tags"],  # Join tags for storage
                    )
                    session.add(post)

        # Commit the session
        await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        load_extended_sample_data("test_users_data.json", "test_posts_data.json")
    )
