import json
from db.engine import async_session
from db.models import DBUser, DBPost


async def load_extended_sample_data(json_file: str):
    async with async_session() as session:
        async with session.begin():
            await session.execute(DBUser.__table__.delete())
            await session.execute(DBPost.__table__.delete())

        with open(json_file, "r") as f:
            data = json.load(f)

        async with session.begin():
            for user_data in data["users"]:
                user = DBUser(
                    id=user_data["id"],
                    email=user_data["email"],
                    username=user_data["username"],
                    password=user_data["password"],
                    role=user_data["role"],
                )
                session.add(user)
                for post_data in user_data["posts"]:
                    post = DBPost(
                        id=post_data["id"],
                        topic=post_data["topic"],
                        content=post_data["content"],
                        user_id=user.id,
                    )
                    session.add(post)
        await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(load_extended_sample_data("test_data.json"))
