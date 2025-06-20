from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import insert, select
from sqlalchemy import func

from app.backend.db_depends import get_db
from app.schemas import CreateReview
from app.models.products import Product
from app.models.category import Category
from app.models.reviews import Review
from app.routers.auth import get_current_user

from fastapi import APIRouter

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/")
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    review = await db.scalars(
        select(Review)
        .join(Product)
        .join(Category)
        .where(
            Review.is_active == True,
            Product.is_active == True,
            Category.is_active == True,
            Product.stock > 0,
        )
    )
    reviews = review.all()
    if reviews is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="There is no reviews"
        )
    return reviews


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_review(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_review: CreateReview,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_customer"):
        product = await db.scalar(
            select(Product).where(Product.slug == create_review.product_slug)
        )
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product found",
            )
        await db.execute(
            insert(Review).values(
                user_id=get_user.get("id"),
                product_id=product.id,
                comment=create_review.comment,
                grade=create_review.grade,
            )
        )
        avg_rating = await db.scalar(
            select(func.avg(Review.grade)).where(
                Review.product_id == product.id,
                Review.is_active == True
            )
        )
        product.rating = avg_rating
        await db.commit()
        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )


@router.get("/{product_slug}")
async def products_reviews(
    db: Annotated[AsyncSession, Depends(get_db)], product_slug: str
):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product no found"
        )

    review = await db.scalars(
        select(Review).where(Review.is_active == True, Review.product_id == product.id)
    )
    reviews = review.all()
    return reviews


@router.delete("/{review_id}")
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    review_id: int,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_admin"):
        review = await db.scalar(
            select(Review).where(
                Review.id == review_id, Review.is_active == True
            )
        )
        if review is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no review found",
            )
        review.is_active = False
        await db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Review delete is successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )
