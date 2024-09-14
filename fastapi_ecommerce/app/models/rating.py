from sqlalchemy import Integer, Boolean, ForeignKey, Column, Float
from app.backend.db import Base


class Rating(Base):
    __tablename__='rating'

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Float)
    user_id = Column(ForeignKey('users.id'))
    product_id = Column(ForeignKey('products.id'))
    is_active = Column(Boolean, default=True)