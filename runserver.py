import os
from HelloFlask import app, db    # Imports the code from HelloFlask/__init__.py       
from flask import Flask
from flask_migrate import Migrate

migrate = Migrate(app, db)


if __name__ == '__main__':
    HOST = os.environ.get('SERVER_HOST', 'localhost')

    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555

    #app.run(HOST, PORT)

    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True, use_reloader=False) #use_reloader on si veut pouvoir changer le css pdt que l'app run

    #REMEMBER TO SWITCH NETWORK PROFILE TYPE IN SETTINGS


