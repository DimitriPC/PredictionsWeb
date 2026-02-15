from typing import List
from sqlalchemy import ForeignKey,ForeignKeyConstraint, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from HelloFlask import app, db
import os
from datetime import date, time


class Individu(db.Model):
    __tablename__ = "individu"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nomComplet: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(60), nullable=False)

    predictions: Mapped[List["Prediction"]] = relationship(back_populates="individu", 
                                                           cascade="all, delete-orphan",
                                                           passive_deletes=True)

class Match(db.Model):
    __tablename__ = "match"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipe1: Mapped[str] = mapped_column(nullable=False)
    equipe2: Mapped[str] = mapped_column(nullable=False)
    stadeCompet: Mapped[str] = mapped_column(nullable=False)
    dateMatch: Mapped[date | None]
    heureMatch: Mapped[time | None]
    resultat: Mapped[str | None]
    scoreEquipe1: Mapped[int | None]
    scoreEquipe2: Mapped[int | None]
    coteEquipe1: Mapped[int | None] = mapped_column(Numeric(6,2))
    coteEquipe2: Mapped[int | None] = mapped_column(Numeric(6,2))

    predictions: Mapped[List["Prediction"]] = relationship(back_populates="game", 
                                                           cascade="all, delete-orphan", 
                                                           passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("equipe1", "equipe2", "stadeCompet"),
    )

class Prediction(db.Model):
    __tablename__ = "prediction"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    individu_id: Mapped[str] = mapped_column(ForeignKey("individu.id", 
                                                                ondelete="CASCADE"), 
                                                     nullable=False)
    idMatch: Mapped[int] = mapped_column(ForeignKey("match.id", 
                                                    ondelete="CASCADE"),
                                         nullable=False)
    resultat: Mapped[str]
    scoreTeam1: Mapped[int]
    scoreTeam2: Mapped[int]
    win: Mapped[int | None]
    autres: Mapped[str | None]
    datePrediction: Mapped[date | None] 

    __table_args__ = (
        UniqueConstraint("individu_id", "idMatch"),
    )

    individu: Mapped["Individu"] = relationship(back_populates="predictions")
    game: Mapped["Match"] = relationship(back_populates="predictions") 





