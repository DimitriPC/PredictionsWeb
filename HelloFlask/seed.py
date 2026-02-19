from HelloFlask import db
from .tables import Equipe, Match, Individu, Prediction
from datetime import datetime

def seed_db():
    # Check if equipes already exist
    if db.session.query(Equipe).first():
        print("Database already seeded.")
        return

    # Insert teams
    equipes = [
        Equipe(name="Real Madrid", logo_url="spain_real-madrid.football-logos.cc"),
        Equipe(name="Barcelona", logo_url="spain_barcelona.football-logos.cc"),
        Equipe(name="Manchester United", logo_url="england_manchester-united.football-logos.cc"),
        Equipe(name="Liverpool", logo_url="england_liverpool.football-logos.cc"),
    ]
    db.session.add_all(equipes)
    db.session.commit()

    # Insert example matches
    match1 = Match(
        equipeHomeId=equipes[0].id,
        equipeAwayId=equipes[1].id,
        stadeCompet="La Liga 1st",
        dateMatch=datetime(2026, 2, 17, 20, 0),
        resultat=None
    )
    match2 = Match(
        equipeHomeId=equipes[2].id,
        equipeAwayId=equipes[3].id,
        stadeCompet="PL",
        dateMatch=datetime(2026, 2, 21, 21, 0),
        resultat=None
    )
    db.session.add_all([match1, match2])
    db.session.commit()

    print("Database seeded successfully.")
