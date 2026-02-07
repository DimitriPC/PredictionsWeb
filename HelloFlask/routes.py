from HelloFlask import app
from flask import Flask, render_template, url_for, redirect, request, session
from flask_bcrypt import bcrypt
import sqlite3, json, os
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from datetime import datetime

THIS_FOLDER = Path(__file__).parent.resolve()
absolute_path = THIS_FOLDER / "can2025DB.db"

app.secret_key = "allo"




@app.route('/', methods=["POST", "GET"])
@app.route('/#', methods=["POST", "GET"])
@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        enteredPassword = request.form["password"].encode('UTF-8')

        with sqlite3.connect(absolute_path) as con:
            cur = con.cursor()

        try:
            storedPassword = cur.execute("SELECT password from individu where nomComplet = ?", (username,)).fetchone()[0]
            if (storedPassword):    #un mot de passe existe pour ce gamertag
                result = bcrypt.checkpw(enteredPassword, storedPassword)
                if (result):
                    session["username"] = username
                    return redirect(url_for("prediction"))
                else:
                    return render_template("failedLogin.html", message="Le mot de passe est incorrect pour ce compte")   
            else:   #aucun mot de passe configure pour le compte
                return render_template("failedLogin.html", message="Aucun mot de passe configure pour ce compte. Veuillez creer un compte")    
        except:
            return render_template("failedLogin.html", message="Ce compte n'existe pas. Le username ou le mot de passe pourrait etre errone")    
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method =="POST":
        username = request.form["username"]
        with sqlite3.connect(absolute_path, timeout=2) as con:
            cur = con.cursor()

        if cur.execute("SELECT * from individu where nomComplet = ?", (username, )).fetchone(): #le gamertag est d j  pr sent dans la basse de donn es
            if checkPasswordExists(cur, username):  #le compte a d j  un password configur 
                return render_template("failedRegister.html", message="Ce compte existe deja. Veuillez vous connecter")    

            else:   #le compte n'a pas encore configur  de password
                passwordBytes = request.form["password"].encode('UTF-8')
                salt = bcrypt.gensalt()
                hash = bcrypt.hashpw(passwordBytes, salt)
                data = (hash, username)
                cur.execute("UPDATE individu set password = ? where nomComplet = ? ", data)
                con.commit()
                con.close()
                session["username"] = username
                return redirect(url_for("prediction"))
        else: #aucun compte associ    ce gamertag encore
            passwordBytes = request.form["password"].encode('UTF-8')
            salt = bcrypt.gensalt()
            hash = bcrypt.hashpw(passwordBytes, salt)
            data = (username, hash)
            cur.execute("insert into individu(nomComplet, password) values (?, ?)", data)
            con.commit()
            con.close()
            session["username"] = username
            return redirect(url_for("prediction"))
    else:
        return render_template("register.html")



@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == "POST":

        username = session["username"]
        matchPK = request.form["matchs"]
        resultat = request.form["resultat"]
        scoreTeam1 = request.form["buts1"]        
        scoreTeam2 = request.form["buts2"]
        autresPred = request.form["autres"]

        team1 = matchPK.split()[0]
        team2 = matchPK.split()[2]
        stadeCompetUnformat = matchPK.split()[3]
        stadeCompet = stadeCompetUnformat.replace("(", "").replace(")", "")

        now = datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(absolute_path, timeout=2) as con:
            cur = con.cursor()

        

        data = (username, team1, team2, stadeCompet, resultat, scoreTeam1, scoreTeam2, autresPred, time)
        sql = "INSERT INTO prediction(individu_nomComplet, equipe1, equipe2, stadeCompet, resultat, scoreTeam1, scoreTeam2, autres, time) values (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(sql, data)
        con.commit()
        con.close()

        return redirect(url_for("ranking"))
    else:
        with sqlite3.connect(absolute_path, timeout=2) as con:
            cur = con.cursor()

        sqlStatement = 'Select equipe1, equipe2, stadeCompet from match;'
        cur.execute(sqlStatement)
        list = cur.fetchall()
        formattedList = []
        
        for match in list:
            equipe1 = match[0]
            equipe2 = match[1]
            stadeCompet = match[2]
            fullString = equipe1 + " " + "vs" + " " + equipe2 + " " + "(" + stadeCompet + ")"
            formattedList.append(fullString)

        
        return render_template("prediction.html", listRows=formattedList) 

@app.route('/ranking', methods=['GET', 'POST'])
def ranking():
    if request.method == "POST":
        return render_template("vide.html")
    else:
        with sqlite3.connect(absolute_path) as con:
            cur = con.cursor()

        sqlStatement = 'SELECT individu_nomComplet AS nom, COUNT(*) AS totalPlayed,SUM(winResultat = 1) AS winResultat,SUM(winScore = 1) AS winScore FROM prediction GROUP BY individu_nomComplet ORDER BY winResultat DESC, winScore DESC;'

        cur.execute(sqlStatement)
        list = cur.fetchall()

        return render_template("ranking.html", listRows=list)

@app.route('/confirmation', methods=['GET', 'POST'])
def confirmation():
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
        with sqlite3.connect(absolute_path) as con:
            cur = con.cursor()

        sqlStatement = 'Select equipe1, equipe2, stadeCompet from match;'
        cur.execute(sqlStatement)
        list = cur.fetchall()
        formattedList = []
        
        for match in list:
            equipe1 = match[0]
            equipe2 = match[1]
            stadeCompet = match[2]
            fullString = equipe1 + " " + "vs" + " " + equipe2 + " " + "(" + stadeCompet + ")"
            formattedList.append(fullString)

        
        return render_template("confirmation.html", listRows=formattedList) 
        

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
    

def checkPasswordExists(cur, gamertag):
    if cur.execute("SELECT password from individu where gamertag = ?", (gamertag, )).fetchone()[0]:
        return True
    else:
        return False

def getPassword(cur, gamertag):
    return cur.execute("SELECT password from individu where gamertag = ?", (gamertag, )).fetchone()[0]


@app.route("/<var>")
def afficher(var):
    return f"<h1>{var}<h1>"



