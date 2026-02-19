from enum import auto
from typing import List
from sqlalchemy import ForeignKey,ForeignKeyConstraint, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from HelloFlask import app, db
from decimal import Decimal
from datetime import date, time, datetime
import os


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
    equipeHomeId: Mapped[int] = mapped_column(ForeignKey("equipe.id"), nullable=False)
    equipeAwayId: Mapped[int] = mapped_column(ForeignKey("equipe.id"), nullable=False)
    stadeCompet: Mapped[str] = mapped_column(nullable=False)
    dateMatch: Mapped[datetime | None]
    resultat: Mapped[str | None]
    scoreEquipe1: Mapped[int | None]
    scoreEquipe2: Mapped[int | None]
    coteEquipe1: Mapped[Decimal | None] = mapped_column(Numeric(6,2))
    coteEquipe2: Mapped[Decimal | None] = mapped_column(Numeric(6,2))

    predictions: Mapped[List["Prediction"]] = relationship(back_populates="game", 
                                                           cascade="all, delete-orphan", 
                                                           passive_deletes=True)
    equipeHome: Mapped["Equipe"] = relationship(back_populates="homeMatches",
                                                foreign_keys=[equipeHomeId])
    equipeAway: Mapped["Equipe"] = relationship(back_populates="awayMatches",
                                                foreign_keys=[equipeAwayId])

    __table_args__ = (
        UniqueConstraint("equipeHomeId", "equipeAwayId", "stadeCompet"),
    )

class Prediction(db.Model):
    __tablename__ = "prediction"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    individu_id: Mapped[int] = mapped_column(ForeignKey("individu.id", 
                                                                ondelete="CASCADE"), 
                                                     nullable=False)
    idMatch: Mapped[int] = mapped_column(ForeignKey("match.id", 
                                                    ondelete="CASCADE"),
                                         nullable=False)
    resultatMatch: Mapped[str]
    scoreTeam1: Mapped[int]
    scoreTeam2: Mapped[int]
    winScore: Mapped[bool | None]
    winOutcome: Mapped[bool | None]
    autres: Mapped[str | None]
    datePrediction: Mapped[datetime | None] 

    __table_args__ = (
        UniqueConstraint("individu_id", "idMatch"),
    )

    individu: Mapped["Individu"] = relationship(back_populates="predictions")
    game: Mapped["Match"] = relationship(back_populates="predictions") 

class Equipe(db.Model):
    __tablename__ = "equipe"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    logo_url: Mapped[str | None]

    homeMatches: Mapped[List["Match"]] = relationship(back_populates="equipeHome",
                                                      foreign_keys="Match.equipeHomeId",)
    awayMatches: Mapped[List["Match"]] = relationship(back_populates="equipeAway",
                                                      foreign_keys="Match.equipeAwayId",)
