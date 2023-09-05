from fastapi import FastAPI
from routers import practise,auth,ezyexplorer
from database import engine
import models
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

models.Base.metadata.create_all(bind=engine)
app=FastAPI()


origins = [
    # "http://localhost:4200"
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(practise.router)
app.include_router(auth.router)
app.include_router(ezyexplorer.router)
if __name__=="__main__":
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)