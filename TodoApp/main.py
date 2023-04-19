from fastapi import FastAPI, Depends
from database import engine
import models
from routers import auth,todos
from company import companyapi, dependencies


app = FastAPI()

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(
    companyapi.router,
    prefix='/company',
    tags = ['company'],
    dependencies=[Depends(dependencies.get_token_header)],
    responses= {401:{'description':'Not Found'}}
)