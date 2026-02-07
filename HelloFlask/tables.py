from typing import List
from sqlalchemy import ForeignKey,ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from HelloFlask import app
import os
from datetime import date, time

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Individu(db.Model):
    __tablename__ = "individu"

    nomComplet: Mapped[str] = mapped_column(primary_key=True)
    password: Mapped[str]

    predictions: Mapped[List["Prediction"]] = relationship(back_populates="individu", 
                                                           cascade="all, delete-orphan",
                                                           passive_deletes=True)

class Match(db.Model):
    __tablename__ = "match"

    equipe1: Mapped[str] = mapped_column(primary_key=True)
    equipe2: Mapped[str] = mapped_column(primary_key=True)
    stadeCompet: Mapped[str] = mapped_column(primary_key=True)
    dateMatch: Mapped[date]
    heureMatch: Mapped[time]
    resultat: Mapped[str]
    scoreEquipe1: Mapped[int]
    scoreEquipe2: Mapped[int]
    coteEquipe1: Mapped[int]
    coteEquipe2: Mapped[int]

    predictions: Mapped[List["Prediction"]] = relationship(back_populates="game", 
                                                           cascade="all, delete-orphan", 
                                                           passive_deletes=True)

class Prediction(db.Model):
    __tablename__ = "prediction"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    individu_nomComplet: Mapped[str] = mapped_column(ForeignKey("individu.nomComplet", 
                                                                ondelete="CASCADE", onupdate="CASCADE"), 
                                                     nullable=False)
    equipe1: Mapped[str] = mapped_column(nullable=False)
    equipe2: Mapped[str] = mapped_column(nullable=False)
    stadeCompet: Mapped[str] = mapped_column(nullable=False)
    resultat: Mapped[str]
    scoreTeam1: Mapped[int]
    scoreTeam2: Mapped[int]
    win: Mapped[int]
    autres: Mapped[str]
    datePrediction: Mapped[date] 

    __table_args__ = (
        ForeignKeyConstraint(
            ["equipe1", "equipe2", "stadeCompet"],
            ["match.equipe1", "match.equipe2", "match.stadeCompet"], 
            ondelete="CASCADE", 
            onupdate="CASCADE",
        ),

        UniqueConstraint("individu_nomComplet", "equipe1", "equipe2", "stadeCompet"),
    )
    individu: Mapped["Individu"] = relationship(back_populates="predictions")
    game: Mapped["Match"] = relationship(back_populates="predictions") 





