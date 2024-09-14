from fastapi import FastAPI
from app.routers import category, products
from app.routers import auth, permission

app = FastAPI()


@app.get('/')
async def welcime() -> dict:
    return {'message': 'My e-commerce app'}


app.include_router(category.router)
app.include_router(products.router)
app.include_router(auth.router)
app.include_router(permission.router)