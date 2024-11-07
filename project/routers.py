from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import not_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Competition, Result

router = APIRouter()

class CompetitionSchemaBase(BaseModel):
   name: str

class CreateCompetitionSchema(CompetitionSchemaBase):
   unit: str

class ResultSchemaBase(BaseModel):
   competition: str
   athlete: str
   value: float

@router.get("/get-competitions")
async def get_competitions(response: Response, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).order_by(Competition.id))
      competitions = obj.scalars().all()

      if not competitions:
         response.status_code = status.HTTP_204_NO_CONTENT
         return 
      
      response.status_code = status.HTTP_200_OK
      body = {"competitions": competitions,
            "status_code": response.status_code}
      
      return body
   except:
      response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      body = {"status_code": response.status_code}
      return body

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
         for result in results[::-1]:
            now_best = result.name
            if now_best not in aux:
               ranking.append(result)
               aux.append(now_best)
 
      return {"ranking": ranking}
   except Exception as e:
      print(e)
   
@router.post("/create-competition")
async def create_competition(response: Response, competition: CreateCompetitionSchema, db: AsyncSession = Depends(get_db)):
   try:   
      new_competition = Competition(name=competition.name, unit=competition.unit.lower())
      db.add(new_competition)
      await db.commit()
      await db.refresh(new_competition)
      
      response.status_code = status.HTTP_201_CREATED
      body = {"competition": new_competition,
            "status_code": response.status_code}

      return body
   except:
      response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      body = {"status_code": response.status_code}
      return body

@router.put("/change-competition-status")
async def change_competition_status(name: str, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name==name))
      competition = obj.scalars().first()
      await db.execute(update(Competition).where(Competition.name==name).values(is_finished=not competition.is_finished))
      await db.commit()
      await db.refresh(competition)
      
      return competition
   except Exception as e:
      print(e)

@router.post("/create-result")
async def create_result(response: Response, result: ResultSchemaBase, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name == result.competition))
      competition = obj.scalars().first()

      if competition.is_finished:
         response.status_code = status.HT
         return {
            "error": "Can't add result to finished competition."
         }
      new_result = Result(
         name=result.athlete,
         value=result.value,
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