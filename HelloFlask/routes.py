from HelloFlask import app, db
from flask import Flask, render_template, url_for, redirect, request, session
from flask_bcrypt import bcrypt
import sqlite3, json, os
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from datetime import datetime
from .tables import Individu, Match, Prediction, Equipe
from sqlalchemy import select, insert, func, Integer
from sqlalchemy.orm import joinedload
from random import randint, choice
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
            session["userId"] = user.id
            return redirect(url_for("prediction"))

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

            session["userId"] = user.id
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

        session["userId"] = new_user.id
        return redirect(url_for("prediction"))

    return render_template("register.html")


@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == "POST":

        userId = int(session["userId"])
        matchID = int(request.form["matchs"])
        resultat = request.form["resultat"]
        scoreTeam1 = int(request.form["buts1"])     
        scoreTeam2 = int(request.form["buts2"])
        autresPred = request.form["autres"]

        pred = Prediction(individu_id=userId, idMatch=matchID, resultat=resultat, scoreTeam1=scoreTeam1, scoreTeam2=scoreTeam2, autres=autresPred, datePrediction=datetime.now())
        db.session.add(pred)
        db.session.commit()

        #add notification to say prediction added
        return redirect(url_for("ranking"))
    else:

        stmt = select(Match).options(joinedload(Match.equipeHome), joinedload(Match.equipeAway))
        all_matches = db.session.scalars(stmt).all()

        pending = []
        finished = []
        for m in all_matches:
            if m.dateMatch:

                if m.dateMatch > datetime.now():
                    pending.append(m)
                else:
                    finished.append(m)
            else:
                pending.append(m)  # no date = predictible

        return render_template("card3.html", pending_matches=pending, finished_matches=finished)

@app.route('/prediction/<matchId>', methods=['GET', 'POST'])
def prediction_match(matchId):
    match = db.session.get(Match, matchId)
    teamHome = db.session.get(Equipe, match.equipeHomeId)
    teamAway = db.session.get(Equipe, match.equipeAwayId)
    return render_template("prediction.html", match=match)

@app.route('/ranking', methods=['GET', 'POST'])
def ranking():
    
    stmt = (
        select(
            Prediction.individu_id,
            func.count().label("nbr_predictions"),
            func.sum(func.cast(Prediction.winScore, Integer)).label("nbr_winScore"),
            func.sum(func.cast(Prediction.winOutcome, Integer)).label("nbr_winOutcome")
        )
        .group_by(Prediction.individu_id)
    )
    ranking = db.session.execute(stmt).all()
    print(ranking, file=sys.stderr)

    return "ranking page"



@app.route('/modification/<int:matchId>', methods=['GET', 'POST'])
def modification(matchId):
    #make prediction visible or invisible only for admin on predictions page
    if request.method == "POST":

        matchPK = request.form["matchs"]
        resultat = request.form.get("resultat")
        scoreTeam1 = request.form["buts1"]        
        scoreTeam2 = request.form["buts2"]
        dateMatch = request.form["date"]

        team1 = matchPK.split()[0]
        team2 = matchPK.split()[2]
        stadeCompetUnformat = matchPK.split()[3]
        stadeCompet = stadeCompetUnformat.replace("(", "").replace(")", "")
        
        

        with sqlite3.connect(absolute_path, timeout=2) as con:
            cur = con.cursor()

        if (scoreTeam1 and scoreTeam2):
            data2 = (resultat, team1, team2, stadeCompet)
            sqlStatement2 = 'UPDATE prediction SET winResultat = CASE WHEN prediction.resultat = ? THEN 1 ELSE 0 END WHERE equipe1 = ? AND equipe2 = ? AND stadeCompet = ?;'
            data4 = (scoreTeam1, scoreTeam2,team1, team2, stadeCompet)
            sqlStatement4 = 'UPDATE match set scoreEquipe1 = ?, scoreEquipe2 = ? where equipe1 = ? and equipe2 = ? and stadeCompet = ?;'
            data5 = (scoreTeam1, scoreTeam2, team1, team2, stadeCompet)
            sqlStatement5 = 'UPDATE prediction SET winScore = CASE WHEN prediction.scoreTeam1 = ? AND prediction.scoreTeam2 = ? THEN 1 ELSE 0 END WHERE equipe1 = ? AND equipe2 = ? AND stadeCompet = ?;'
            cur.execute(sqlStatement2, data2)
            cur.execute(sqlStatement4, data4)
            cur.execute(sqlStatement5, data5)
        
        if not (scoreTeam1 or scoreTeam2):
            data3 = (dateMatch, team1, team2, stadeCompet)
            sqlStatement3 = 'update match set dateMatch = ? where equipe1 = ? and equipe2 = ? and stadeCompet = ?;'
            cur.execute(sqlStatement3, data3)
        
        con.commit()
        con.close()

        return redirect(url_for("ranking"))

    else:
        match = db.session.get(Match, matchId)
        return render_template("modification.html", match=match) 
        















@app.route('/resultat', methods=['GET', 'POST'])
def resultat():
    with sqlite3.connect(absolute_path) as con:
        cur = con.cursor()

    sqlStatement = 'SELECT equipe1, equipe2, stadeCompet from match where dateMatch is not null ORDER BY dateMatch DESC;'

    cur.execute(sqlStatement)
    list = cur.fetchall()
    print(list)
    
    sqlStatement2 = 'SELECT individu_nomComplet, equipe1, equipe2, stadeCompet, scoreTeam1, scoreTeam2, autres FROM prediction;'
    
    cur.execute(sqlStatement2)
    listPredictions = cur.fetchall()

    return render_template("resultat.html", listRows=list, predRows=listPredictions)


 


