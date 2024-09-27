import json
from db.engine import async_session
from db.models import DBUser, DBPost


async def load_extended_sample_data(test_users_data: str, test_posts_data: str):
    async with async_session() as session:
        async with session.begin():
            await session.execute(DBUser.__table__.delete())
            await session.execute(DBPost.__table__.delete())

        with open(test_users_data, "r") as f:
            data = json.load(f)

            async with session.begin():
                for user_data in data:
                    user = DBUser(
                        email=user_data["email"],
                        username=user_data["username"],
                        password=user_data["password"],
                        profile_picture=user_data["profile_picture"],
                        role=user_data["role"],
                    )
                    session.add(user)
        with open(test_posts_data, "r") as f:
            data = json.load(f)
            for post_data in data:
                post = DBPost(
                    topic=post_data["topic"],
                    content=post_data["content"],
                    user_id=post_data["user_id"],
                    tags=post_data["tags"],
                )
                session.add(post)
        await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        load_extended_sample_data("test_users_data.json", "test_posts_data.json")
    )
