from fastapi import APIRouter, Depends, Response, status, HTTPException
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
         response.status_code = status.HTTP_404_NOT_FOUND
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
         )
      
      response.status_code = status.HTTP_200_OK
      response.body = {
         "competitions": competitions,
      }
      return response.body
   except Exception as e:
      response.body = {"error": e}
      return response.body

@router.get("/get-ranking/{name}")
async def get_ranking(response: Response, name: str, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name==name))
      competition = obj.scalars().all()

      if not competition:
         response.status_code = status.HTTP_404_NOT_FOUND
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
         )

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
 
      response.status_code = status.HTTP_200_OK
      response.body = {
         "ranking": ranking
      }

      return response.body
   except Exception as e:
      response.body = {"error": e}
      return response.body

@router.put("/change-competition-status")
async def change_competition_status(response: Response, competition: CompetitionSchemaBase, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name==competition.name))
      competitions = obj.scalars().all()

      if not competitions:
         response.status_code = status.HTTP_404_NOT_FOUND
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
         )

      await db.execute(update(Competition).where(Competition.name==competition.name).values(is_finished=not competitions[0].__dict__["is_finished"]))
      await db.commit()
      await db.refresh(competitions[0])
      
      response.status_code = status.HTTP_200_OK
      response.body = {
         "competition": competitions[0]
      }
      
      return response.body
   except Exception as e:
      response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      response.body = {"error": e}
      return response.body

@router.post("/create-competition")
async def create_competition(response: Response, competition: CreateCompetitionSchema, db: AsyncSession = Depends(get_db)):
   try:   
      new_competition = Competition(name=competition.name, unit=competition.unit.lower())
      print(new_competition)

      db.add(new_competition)
      await db.commit()
      await db.refresh(new_competition)
      
      response.status_code = status.HTTP_201_CREATED
      response.body = {
         "competition": new_competition,
      }
      return response.body
   except ValueError as e:
      response.status_code = status.HTTP_409_CONFLICT
      response.body = {"error": e.args}
      return response.body
   except Exception as e:
      response.body = {"error": e}
      return response.body

@router.post("/create-result")
async def create_result(response: Response, result: ResultSchemaBase, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name == result.competition))
      competition = obj.scalars().all()

      if not competition:
         response.status_code = status.HTTP_404_NOT_FOUND
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
         )

      if competition[0].__dict__["is_finished"]:
         response.status_code = status.HTTP_409_CONFLICT
         response.body = {
            "error": "Competition is already finished!",
         }
         return response.body

      new_result = Result(
         name=result.athlete,
         value=result.value,
         competition_id=competition.id
      )
      db.add(new_result)
      await db.commit()
      await db.refresh(new_result)

      response.status_code = status.HTTP_200_OK
      response.body = {
         "result": new_result,
      }
      return response.body
   except Exception as e:
      response.body = {"error": e}
      return response.body