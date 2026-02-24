from HelloFlask import app, db
from flask import Flask, render_template, url_for, redirect, request, session
from flask_bcrypt import bcrypt
import sqlite3, json, os
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from datetime import datetime, timedelta
from .tables import Individu, Match, Prediction, Equipe
from sqlalchemy import select, insert, func, Integer
from sqlalchemy.orm import joinedload
from random import randint, choice
from flask_login import login_user, login_required, logout_user, current_user
import sys


THIS_FOLDER = Path(__file__).parent.resolve()
absolute_path = THIS_FOLDER / "can2025DB.db"

app.secret_key = "allo"

@app.route('/', methods=["POST", "GET"])
@app.route('/#', methods=["POST", "GET"])
@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        enteredPassword = request.form["password"].encode("utf-8")

        stmt = select(Individu).where(Individu.nomComplet == username)
        user = db.session.scalars(stmt).first()

        # account does not exist
        if not user:
            return render_template(
                "failedLogin.html",
                message="Ce compte n'existe pas. Le username ou le mot de passe pourrait etre errone"
            )

        # account exists but no password
        if not user.password:
            return render_template(
                "failedLogin.html",
                message="Aucun mot de passe configure pour ce compte. Veuillez creer un compte"
            )

        # check password
        if bcrypt.checkpw(enteredPassword, user.password.encode("utf-8")):
            login_user(user)
            if (user.nomComplet == "Dimipc"):
                user.is_admin = True;
                session["is_admin"] = user.is_admin
            next = request.args.get("next")
            return redirect(next or url_for('prediction'))

        return render_template(
            "failedLogin.html",
            message="Le mot de passe est incorrect pour ce compte"
        )

    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        user = Individu.query.filter_by(nomComplet=username).first()

        # If user already exists
        if user:

            # If password already configured
            if user.password:
                return render_template(
                    "failedRegister.html",
                    message="Ce compte existe deja. Veuillez vous connecter"
                )

            # User exists but no password yet
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password, salt)

            user.password = hashed
            db.session.commit()

            login_user(user)
            return redirect(url_for("prediction"))

        # User does not exist → create new one
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt).decode("utf-8")

        new_user = Individu(
            nomComplet=username,
            password=hashed
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("prediction"))

    return render_template("register.html")


@app.route('/prediction', methods=['GET', 'POST'])
@login_required
def prediction():
    # Montreal is UTC-5
    now = datetime.utcnow() - timedelta(hours=5)

    to_do = Match.query.filter(
        Match.dateMatch > now,
        ~Match.predictions.any(Prediction.individu_id == current_user.id)
    ).all()

    pending = Match.query.filter(
        Match.dateMatch > now,
        Match.predictions.any(Prediction.individu_id == current_user.id)
    ).all()

    finished = Match.query.filter(
        Match.dateMatch <= now
    ).all()

    return render_template("card.html", toDo_matches = to_do, pending_matches=pending, finished_matches=finished)

        

@app.route('/prediction/<int:matchId>', methods=['GET', 'POST'])
@login_required
def prediction_match(matchId):
    if request.method == "POST":

        userId = current_user.id
        resultat = request.form["resultat"]        
        scoreTeam1 = int(request.form["buts1"])     
        scoreTeam2 = int(request.form["buts2"])
        autresPred = request.form["autres"]

        pred = Prediction(individu_id=userId, idMatch=matchId, resultatMatch=resultat, scoreTeam1=scoreTeam1, 
                          scoreTeam2=scoreTeam2, autres=autresPred, datePrediction=datetime.now())
        db.session.add(pred)
        db.session.commit()

        #add notification to say prediction added
        return redirect(url_for("ranking"))
    else:
        match = db.session.get(Match, matchId)
        teamHome = db.session.get(Equipe, match.equipeHomeId)
        teamAway = db.session.get(Equipe, match.equipeAwayId)
        return render_template("prediction.html", match=match)

@app.route('/ranking', methods=['GET', 'POST'])
def ranking():
    
    stmt = (
        select(
            Individu.nomComplet,
            Prediction.individu_id,
            func.count().label("nbr_predictions"),
            func.sum(func.cast(Prediction.winScore, Integer)).label("nbr_winScore"),
            func.sum(func.cast(Prediction.winOutcome, Integer)).label("nbr_winOutcome")
        )
        .join(Individu, Individu.id == Prediction.individu_id)
        .group_by(Individu.nomComplet, Prediction.individu_id)
        .order_by(
        (func.sum(func.cast(Prediction.winScore, Integer)) +
         func.sum(func.cast(Prediction.winOutcome, Integer))).desc()
        )
    )
        
    
    joueurs = db.session.execute(stmt).all()
    return render_template("ranking.html", joueurs=joueurs)

#admin route
@app.route('/modification/<int:matchId>', methods=['GET', 'POST'])
@login_required
def modification(matchId):
    #make prediction visible or invisible only for admin on predictions page
    #its possible to have different score prediction to outcome prediction
    if request.method == "POST":

        match = db.session.get(Match, matchId)
        scoreTeam1 = request.form.get("buts1")      
        scoreTeam2 = request.form.get("buts2")
        dateMatch = request.form.get("date")

        
        #update match
        if scoreTeam1 is not None and scoreTeam2 is not None:
            match.scoreEquipe1 = int(scoreTeam1)
            match.scoreEquipe2 = int(scoreTeam2)

        #give win/lose to all
        if (scoreTeam1 and scoreTeam2):
            for prediction in match.predictions:
                prediction.winScore = True if (prediction.scoreTeam1 == match.scoreEquipe1 and prediction.scoreTeam2 == match.scoreEquipe2) else False
                prediction.winOutcome = True if (prediction.resultatMatch == match.result) else False
        
        if (dateMatch):
            dateObj = datetime.strptime(dateMatch, "%Y-%m-%dT%H:%M")
            match.dateMatch = dateObj

        db.session.commit()

        #Notification to say match was updated
        return redirect(url_for("ranking"))
    else:
        match = db.session.get(Match, matchId)
        return render_template("modification.html", match=match) 

#admin route
@app.route('/addGame', methods=['GET', 'POST'])
@login_required
def addGame():
    if request.method == "POST":
        form_type = request.form.get("form_type")

        if (form_type == "add_team"):
            teamName = request.form.get("team_name")
            logoUrl = request.form.get("logo_url")

            newTeam = Equipe(name=teamName, logo_url=logoUrl)
            db.session.add(newTeam)
            db.session.commit()

        if (form_type == "add_game"):
            homeTeam = int(request.form.get("home_team"))
            awayTeam = int(request.form.get("away_team"))
            stadeCompet = request.form.get("stage")

            date = request.form.get("match_datetime")
            if (date):
                date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M")

            newMatch = Match(equipeHomeId=homeTeam, equipeAwayId=awayTeam, stadeCompet=stadeCompet, dateMatch=date_obj)
            db.session.add(newMatch)
            db.session.commit()

        return redirect(url_for("addGame"))
    else:
        stmt = select(Equipe)
        equipes = db.session.scalars(stmt).all()
        return render_template("addGame.html", teams=equipes)

@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("login"))