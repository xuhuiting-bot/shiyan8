import os

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI ='sqlite:///' + os.path.join(basedir, 'breakout_game.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False