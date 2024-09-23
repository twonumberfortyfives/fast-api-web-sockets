from sqlalchemy import Integer, Column, String, ForeignKey
from sqlalchemy.orm import relationship

from db.engine import Base


class DBUser(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=False)


class DBPost(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    content = Column(String(500), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship(DBUser)
