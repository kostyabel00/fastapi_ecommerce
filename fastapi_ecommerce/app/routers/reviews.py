from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update

from app.backend.db_depends import get_db
from app.models import Product
from app.routers.auth import get_current_user
from app.models.rating import Rating
from app.models.review import Review
from app.schemas import CreateReview, CreateRating


router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/')
async def get_all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Review).where(Review.is_active == True))
    ratings = await db.scalars(select(Rating).where(Rating.is_active == True))
    if ratings is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no ratings and reviews'
        )
    return reviews.all(), ratings.all()


@router.get('/product_reviews/{product_slug}')
async def get_product_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                              product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    prod_reviews = await db.scalars(select(Review).where(Review.product_id == product.id, Review.is_active == True))
    prod_rating = await db.scalars(select(Rating).where(Rating.product_id == product.id, Rating.is_active == True))
    if prod_reviews is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no ratings and reviews'
        )
    return prod_rating.all(), prod_reviews.all()


@router.post('/add_review/{product_slug}')
async def add_review(db: Annotated[AsyncSession, Depends(get_db)],
                     create_review: CreateReview, create_rating: CreateRating,
                     product_slug: str,
                     get_user: Annotated[dict, Depends(get_current_user)]):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if get_user.get('username'):
        await db.execute(insert(Rating).values(
            grade=create_rating.grade,
            user_id=get_user.get('id'),
            product_id=product.id
        ))
        await db.execute(insert(Review).values(
            user_id=get_user.get('id'),
            product_id=product.id,
            rating_id=create_review.rating_id,
            comment=create_review.comment))
        await db.commit()
        ratings = await db.scalars(select(Rating).where(Rating.product_id == product.id, Rating.is_active == True))
        rating_counter, sum = 0, 0
        for rating in ratings:
            if rating.is_active:
                rating_counter += 1
                sum += rating.grade
        amount = round(sum/rating_counter, 2)
        await db.execute(update(Product).where(Product.slug == product_slug).values(rating=amount))
        await db.commit()
        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful',
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to used this method'
        )


@router.delete('/delete')
async def delete_review(db: Annotated[AsyncSession, Depends(get_db)],
                        get_user: Annotated[AsyncSession, Depends(get_current_user)],
                        rating_id: int, review_id: int):
    if get_user.get('is_admin'):
        rating = await db.scalar(select(Rating).where(Rating.id == rating_id))
        review = await db.scalar(select(Review).where(Review.id == review_id))
        if not review or not rating or not review.is_active or not rating.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Rating and review mot found'
            )
        await db.execute(update(Rating).where(Rating.id == rating_id).values(is_active=False))
        await db.execute(update(Review).where(Review.id == review_id).values(is_active=False))
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Product delete is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You can not use this method'
        )

