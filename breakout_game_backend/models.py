from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    scores = db.relationship('Score', backref='player', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score_value = db.Column(db.Integer, nullable=False)
    game_date = db.Column(db.DateTime, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)