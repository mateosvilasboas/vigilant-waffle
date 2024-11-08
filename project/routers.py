import sqlalchemy
from operator import itemgetter
from typing import List
from fastapi import APIRouter, Depends, Response, status, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import Competition, Athlete, Score
from utils import format_error

router = APIRouter()

class CompetitionSchemaBase(BaseModel):
   name: str

class CreateCompetitionSchema(CompetitionSchemaBase):
   unit: str
   number_of_attempts: int

class AthleteSchemaBase(BaseModel):
   competition: str
   athlete: str
   scores: List[float]

@router.get("/get-competitions")
async def get_competitions(response: Response, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).order_by(Competition.id))
      competitions = obj.scalars().all()

      if not competitions:
         response.status_code = status.HTTP_404_NOT_FOUND
         response.body = format_error(status_code=status.HTTP_404_NOT_FOUND, error="competitions not found")
         return response.body
      
      response.status_code = status.HTTP_200_OK
      response.body = {
         "competitions": competitions,
      }
      return response.body
   except Exception as e:
      response.body = format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))
      return response.body

@router.get("/get-ranking/{name}")
async def get_ranking(response: Response, name: str, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name==name))
      competition = obj.scalars().all()

      if not competition:
         response.status_code = status.HTTP_404_NOT_FOUND
         response.body = format_error(status_code=status.HTTP_404_NOT_FOUND, error="competition not found")
         return response.body

      athletes = competition[0].__dict__["athletes"]
      unit = None
      ranking = []
      aux = []

      if competition[0].unit.name == "meters":
         unit = "meters"
         for athlete in athletes:
            if athlete.id not in aux:
               ranking.append({
                  "id": athlete.id,
                  "athlete": athlete.name,
                  "best_score": athlete.scores[0].value})
               aux.append(athlete.id)
         ranking.sort(key=itemgetter("best_score"), reverse=True)
      
      if competition[0].unit.name == "seconds":
         unit = "seconds"
         for athlete in athletes:
            if athlete.id not in aux:
               ranking.append({
                  "id": athlete.id,
                  "athlete": athlete.name,
                  "best_score": athlete.scores[-1].value})
               aux.append(athlete.id)
         ranking.sort(key=itemgetter("best_score"))

      response.status_code = status.HTTP_200_OK
      response.body = {
         "is_finished": competition[0].is_finished,
         "unit": unit,
         "ranking": ranking
      }

      return response.body
   except Exception as e:
      response.body = format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))
      return response.body

@router.put("/change-competition-status")
async def change_competition_status(response: Response, body: CompetitionSchemaBase, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name==body.name.lower()))
      competition = obj.scalars().all()

      if not competition:
         response.status_code = status.HTTP_404_NOT_FOUND
         response.body = format_error(status_code=status.HTTP_404_NOT_FOUND, error="competition not found")
         return response.body

      await db.execute(update(Competition).where(Competition.name==competition[0].name.lower()).values(is_finished=not competition[0].__dict__["is_finished"]))
      await db.commit()
      await db.refresh(competition[0])
      
      response.status_code = status.HTTP_200_OK
      response.body = {
         "competition": competition[0]
      }
      
      return response.body
   except Exception as e:
      response.body = format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))
      return response.body

@router.post("/create-competition")
async def create_competition(response: Response, body: CreateCompetitionSchema, db: AsyncSession = Depends(get_db)):
   try:   
      new_competition = Competition(name=body.name.lower(), unit=body.unit.lower(), number_of_attempts=body.number_of_attempts)

      db.add(new_competition)
      await db.commit()
      await db.refresh(new_competition)
      
      response.status_code = status.HTTP_201_CREATED
      response.body = {
         "competition": new_competition,
      }
      return response.body
   except ValueError as e:
      response.body = format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))
      return response.body
   except IntegrityError as e:
      response.body = format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error="competition name must be unique")
      return response.body
   except Exception as e:
      response.body = format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))
      return response.body

@router.post("/create-result")
async def create_result(response: Response, body: AthleteSchemaBase, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).where(Competition.name == body.competition.lower()))
      competition = obj.scalars().all()

      if not competition:
         response.status_code = status.HTTP_404_NOT_FOUND
         response.body = format_error(status_code=status.HTTP_404_NOT_FOUND, error="competition not found")
         return response.body
      
      if competition[0].__dict__["is_finished"]:
         response.status_code = status.HTTP_409_CONFLICT
         response.body = {
            "error": "competition is already finished",
         }
         return response.body
      
      if len(body.scores) != competition[0].number_of_attempts:
         response.status_code = status.HTTP_409_CONFLICT
         response.body = format_error(status_code=status.HTTP_404_NOT_FOUND, error="count of scores is different than number of attempts of competiton")
         return response.body

      new_result = Athlete(
         name=body.athlete,
         competition_id=competition[0].id,
      )

      for score in body.scores:
         new_score = Score(
            value=score,
            athlete_id=new_result.id
         )
         new_result.scores.append(new_score)

      db.add(new_result)
      await db.commit()
      await db.refresh(new_result)

      response.status_code = status.HTTP_200_OK
      response.body = {
         "result": new_result,
      }
      return response.body
   except Exception as e:
      response.body = format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))
      return response.body