from operator import itemgetter
from typing import List
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
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

class CompetitionUpdateSchemaBase(BaseModel):
   id: int   

class CreateCompetitionSchema(CompetitionSchemaBase):
   unit: str
   number_of_attempts: int

class AthleteSchemaBase(BaseModel):
   competition: str
   athlete: str
   scores: List[float]

@router.get("/get-competitions", status_code=status.HTTP_200_OK)
async def get_competitions(response: Response, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).
                             order_by(Competition.id))
      competitions = obj.scalars().all()

      if not competitions:
         return JSONResponse(
            format_error(status_code=status.HTTP_404_NOT_FOUND, 
                         error="competitions not found"),
            status_code=status.HTTP_404_NOT_FOUND)
         
      return {"competitions": competitions}
   except Exception as e:
         return JSONResponse(
            format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                         error=str(e)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/get-ranking/{name}", status_code=status.HTTP_200_OK)
async def get_ranking(response: Response, name: str, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).
                             where(Competition.name==name.lower().strip()))
      competition = obj.scalars().all()

      if not competition:
         return JSONResponse(
            format_error(status_code=status.HTTP_404_NOT_FOUND, 
                         error="competition not found"),
            status_code=status.HTTP_404_NOT_FOUND)

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

      return {
         "is_finished": competition[0].is_finished,
         "unit": unit,
         "ranking": ranking
      }
   except Exception as e:
      return JSONResponse(
         format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                      error=str(e)),
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.put("/change-competition-status", status_code=status.HTTP_200_OK)
async def change_competition_status(response: Response, body: CompetitionUpdateSchemaBase, db: AsyncSession = Depends(get_db)):
   try:
      obj = await db.execute(select(Competition).
                             where(Competition.id==body.id))
      competition = obj.scalars().all()

      if not competition:
         return JSONResponse(
            format_error(status_code=status.HTTP_404_NOT_FOUND, 
                         error="competition not found"),
            status_code=status.HTTP_404_NOT_FOUND)

      await db.execute(update(Competition).
                       where(Competition.id==competition[0].id).
                       values(is_finished=not competition[0].__dict__["is_finished"]))
      await db.commit()
      await db.refresh(competition[0])
      
      return  {
         "competition": competition[0],
      }
   except Exception as e:
      return JSONResponse(
         format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                      error=str(e)),
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/create-competition", status_code=status.HTTP_201_CREATED)
async def create_competition(response: Response, body: CreateCompetitionSchema, db: AsyncSession = Depends(get_db)):
   try:
      if not body.name:
         return JSONResponse(
            format_error(status_code=status.HTTP_400_BAD_REQUEST, 
                         error="competition must have a name"),
            status_code=status.HTTP_400_BAD_REQUEST)

      new_competition = Competition(name=body.name.lower().strip(),
                                    unit=body.unit.lower().strip(), 
                                    number_of_attempts=body.number_of_attempts)

      db.add(new_competition)
      await db.commit()
      await db.refresh(new_competition)
   
      return {
         "competition": new_competition,
      }
   
   except ValueError as e:
      return JSONResponse(
         format_error(status_code=status.HTTP_409_CONFLICT, 
                      error="only accepts 'meters' or 'seconds'"),
         status_code=status.HTTP_409_CONFLICT)
   except IntegrityError as e:
      return JSONResponse(
         format_error(status_code=status.HTTP_409_CONFLICT, 
                      error="name must be unique"),
         status_code=status.HTTP_409_CONFLICT)
   except Exception as e:
      return JSONResponse(
         format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                      error=str(e)),
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/create-result", status_code=status.HTTP_201_CREATED)
async def create_result(response: Response, body: AthleteSchemaBase, db: AsyncSession = Depends(get_db)):
   try:

      obj = await db.execute(select(Competition).
                             where(Competition.name == body.competition.lower().strip()))
      competition = obj.scalars().all()
      
      if not competition:
         return JSONResponse(
            format_error(status_code=status.HTTP_404_NOT_FOUND, error="competition not found"),
            status_code=status.HTTP_404_NOT_FOUND)
      
      if competition[0].__dict__["is_finished"]:
         return JSONResponse(
            format_error(status_code=status.HTTP_409_CONFLICT, error="competition is already finished'"),
            status_code=status.HTTP_409_CONFLICT)
      
      if len(body.scores) != competition[0].number_of_attempts:
         return JSONResponse(
            format_error(status_code=status.HTTP_409_CONFLICT, 
                         error="count of scores is different than number of attempts of competiton"),
            status_code=status.HTTP_409_CONFLICT)

      if not body.athlete:
         return JSONResponse(
            format_error(status_code=status.HTTP_400_BAD_REQUEST, 
                         error="athlete must have a name"),
            status_code=status.HTTP_400_BAD_REQUEST)

      new_result = Athlete(
         name=body.athlete.strip(),
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

      return {"new_result": new_result}
   except Exception as e:
      return JSONResponse(
         format_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                      error=str(e)),
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)