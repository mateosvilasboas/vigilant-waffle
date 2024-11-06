import enum
from typing import List

from sqlalchemy import Enum, ForeignKey 
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
    results: Mapped[List["Result"]] = relationship(back_populates="competition", init=False, lazy="selectin")

    @validates("unit")
    def validate_unit(self, key, unit):
        if unit not in CompetitionUnits._member_names_:
            raise ValueError("Only accepts 'meters' or 'seconds'")
        return unit

@table_registry.mapped_as_dataclass
class Result:
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str]
    value: Mapped[float]
    unit: Mapped[str]
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), init=False)
    competition: Mapped["Competition"] = relationship(back_populates="results", lazy="selectin")

