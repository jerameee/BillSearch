from fastapi import APIRouter, FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker as SessionMaker
from app.models.bill import Bill, engine

app = FastAPI()
router = APIRouter()


def get_db():
    SessionLocal = SessionMaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search")
async def search(query: str, db: Session = Depends(get_db)):
    results = db.query(Bill).filter(Bill.content.contains(query)).all()
    return {"results": [{"title": bill.title, "content": bill.content} for bill in results]}

app.include_router(router)
