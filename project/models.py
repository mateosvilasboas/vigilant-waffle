import enum

from typing import List

from sqlalchemy import Enum, ForeignKey, asc, desc, text
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship, validates

table_registry = registry()

class CompetitionUnits(enum.Enum):
    seconds = "seconds"
    meters = "meters"

@table_registry.mapped_as_dataclass
class Competition:
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(unique=True)
    unit: Mapped[CompetitionUnits] = mapped_column(Enum(CompetitionUnits),
                                                   nullable=False)
    is_finished: Mapped[bool] = mapped_column(default=False)
    athletes: Mapped[List["Athlete"]] = relationship(init=False, order_by=desc(text("athletes.value")), lazy="selectin")

    @validates("unit")
    def validate_unit(self, key, unit):
        if unit not in CompetitionUnits._member_names_:
            raise ValueError("Only accepts 'meters' or 'seconds'")
        return unit

@table_registry.mapped_as_dataclass
class Athlete:
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str]
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    scores: Mapped[List["Score"]] = relationship(init=False, order_by=desc(text("scores.value")), lazy="selectin")

@table_registry.mapped_as_dataclass
class Score:
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    value: Mapped[float]
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))