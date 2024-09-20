from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.bill import Bill, engine
from sqlalchemy.orm import sessionmaker

router = APIRouter()

def get_db():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/search")
async def search(query: str, db: Session = Depends(get_db)):
    results = db.query(Bill).filter(Bill.content.contains(query)).all()
    return {"results": [{"title": bill.title, "content": bill.content} for bill in results]}