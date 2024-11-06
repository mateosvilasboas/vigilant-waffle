from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Competition

router = APIRouter(prefix="/competition", tags=["competition"])

class CompetitionSchemaBase(BaseModel):
   name: str
   unit: str

class ResultSchemaBase(BaseModel):
   pass

@router.get("/get-competitions")
async def get_competitions(db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).order_by(Competition.id))
      result = obj.scalars().all()
      print(result)
      return {"competitions": result}
   except Exception as e:
      print(e)

@router.get("/get-competition/{competition}")
async def get_competition(competition: str, db: AsyncSession = Depends(get_db)):
   pass
   # try:
   #    obj = await db.execute(select(Competition).where(Competition.name == competition))
   #    result = obj.scalars().all()
   #    return {"competition": result}
   # except Exception as e:
   #    print(e)
   
@router.post("/create-competition")
async def create_competition(competition: CompetitionSchemaBase, db: AsyncSession = Depends(get_db)):
   try:   
      new_competition = Competition(name=competition.name, unit=competition.unit)
      db.add(new_competition)
      await db.commit()
      await db.refresh(new_competition)
      return competition
   except Exception as e:
      print(e)

@router.post("/create-result")
async def create_result(result: ResultSchemaBase, db: AsyncSession = Depends(get_db)):
   pass