from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Competition, Result

router = APIRouter()

class CompetitionSchemaBase(BaseModel):
   name: str
   unit: str

class ResultSchemaBase(BaseModel):
   competition: str
   athlete: str
   value: float
   unit: str

@router.get("/get-competitions")
async def get_competitions(db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).order_by(Competition.id))
      competitions = obj.scalars().all()     
      return {"competitions": competitions}
   except Exception as e:
      print(e)

@router.get("/get-ranking/{name}")
async def get_ranking(name: str, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name==name))
      competition = obj.scalars().all()
      results = competition[0].__dict__["results"]

      ranking = []
      aux = []

      if competition[0].unit.name == "meters":
         for result in results:
            now_best = result.name
            if now_best not in aux:
               ranking.append(result)
               aux.append(now_best)
      
      if competition[0].unit.name == "seconds":
         for result in results:
            now_best = result.name
            if now_best not in aux:
               ranking.append(result)
               aux.append(now_best)
         ranking = ranking[::-1]
 
      return {"ranking": ranking}
   except Exception as e:
      print(e)
   
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

@router.put("/change-competition-status")
async def change_competition_status(competition: CompetitionSchemaBase, db: AsyncSession = Depends(get_db)):
   pass

@router.post("/create-result")
async def create_result(result: ResultSchemaBase, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name == result.competition))
      competition = obj.scalars().first()
      new_result = Result(
         name=result.athlete,
         value=result.value,
         unit=result.unit,
         competition_id=competition.id
      )
      if competition.is_finished:
         raise ValueError("Can't create result, competition is finished!")
      db.add(new_result)
      await db.commit()
      await db.refresh(new_result)
      return result
   except Exception as e:
      print(e)