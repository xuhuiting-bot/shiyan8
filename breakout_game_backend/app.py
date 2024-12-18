from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
from flask_cors import CORS
from dotenv import load_dotenv
import os
from email_validator import validate_email, EmailNotValidError

# 加载.env文件中的配置到环境变量（开发环境常用）
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"])  # 修改为与前端请求的端口一致，确保跨域正常
# CORS(app, origins=["http://localhost:63342"])  # 修改为与前端请求的端口一致，确保跨域正常

# 设置日志级别为DEBUG，这样所有级别的日志都会显示
app.logger.setLevel(logging.DEBUG)

# 配置数据库相关设置，使用 SQLite 数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breakout_game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 在应用上下文环境中创建数据库表（如果不存在）
with app.app_context():
    db.create_all()


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    # 不在这里定义 relationship 作为列
    scores = db.relationship('Score', backref='player', lazy=True, cascade='all, delete-orphan')


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score_value = db.Column(db.Integer, nullable=False)
    game_date = db.Column(db.DateTime, default=datetime.utcnow)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    # 'player' 是反向引用，指向 Player 模型


# 添加根路由
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Breakout Game API!"}), 200


@app.route('/players', methods=['POST'])
def add_player():
    """
    添加玩家接口，接收用户名和邮箱信息，验证后将玩家信息存入数据库。
    """
    app.logger.debug("Received add player request")  # 记录更详细的日志信息，方便排查是否收到请求
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    if not username or not email:
        app.logger.warning("Username or email is missing in the request.")  # 记录缺少必要参数的情况
        return jsonify({"message": "Username and email are required"}), 400
    try:
        # 验证邮箱格式
        valid_email = validate_email(email).email
    except EmailNotValidError as e:
        app.logger.error(f"Invalid email format: {str(e)}")  # 记录邮箱格式验证失败的具体错误信息
        return jsonify({"message": "Invalid email format"}), 400
    new_player = Player(username=username, email=valid_email)
    try:
        db.session.add(new_player)
        db.session.commit()
        app.logger.info("Player added successfully to the database.")  # 记录数据库添加成功的情况
        return jsonify({"message": "Player added successfully", "player_id": new_player.id}), 201
    except Exception as e:
        app.logger.error(f"Database error when adding player {username}: {str(e)}")  # 添加用户名信息到日志记录，方便定位具体玩家添加失败的原因
        db.session.rollback()  # 出现异常时回滚事务，避免数据不一致
        return jsonify({"message": f"Failed to add player due to database error: {str(e)}"}), 500


@app.route('/scores', methods=['POST'])
def add_score():
    """
    @api {post} /scores 添加游戏分数接口
    @apiName AddScore
    @apiGroup Scores
    @apiParam {Integer} player_id 玩家ID，必填，需对应存在的玩家
    @apiParam {Integer} score_value 分数值，必填
    @apiSuccess {String} message 操作结果消息，成功时为 "Score added successfully"
    @apiError 400 缺少玩家ID或分数值参数
    @apiError 404 玩家不存在
    @apiError 500 数据库操作出现内部错误
    """
    data = request.get_json()
    player_id = data.get('player_id')
    score_value = data.get('score_value')
    if not player_id or not score_value:
        app.logger.warning("Player ID or score value is missing in the request.")  # 记录缺少必要参数的情况
        return jsonify({"message": "Player ID and score value are required"}), 400
    player = Player.query.get(player_id)
    if not player:
        app.logger.warning(f"Player with ID {player_id} not found when trying to add score.")  # 记录玩家不存在的情况
        return jsonify({"message": "Player not found"}), 404
    new_score = Score(score_value=score_value, game_date=datetime.now(), player_id=player_id)
    try:
        db.session.add(new_score)
        db.session.commit()
        app.logger.info("Score added successfully to the database.")  # 记录分数添加成功的情况
        return jsonify({"message": "Score added successfully"}), 201
    except Exception as e:
        app.logger.error(f"Database error when adding score for player {player_id}: {str(e)}")  # 记录添加分数时数据库出错的具体情况
        db.session.rollback()
        return jsonify({"message": f"Failed to add score due to database error: {str(e)}"}), 500


@app.route('/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """
    @api {get} /players/<int:player_id> 获取玩家信息接口
    @apiName GetPlayer
    @apiGroup Players
    @apiSuccess {Integer} id 玩家ID
    @apiSuccess {String} username 玩家用户名
    @apiSuccess {String} email 玩家邮箱
    @apiError 404 玩家不存在
    """
    player = Player.query.get(player_id)
    if not player:
        app.logger.warning(f"Player with ID {player_id} not found when trying to get player info.")  # 记录玩家不存在的情况
        return jsonify({"message": "Player not found"}), 404
    return jsonify({
        "id": player.id,
        "username": player.username,
        "email": player.email
    }), 200


@app.route('/players/<int:player_id>/scores', methods=['GET'])
def get_player_scores(player_id):
    """
    @api {get} /players/<int:player_id>/scores 获取玩家分数历史记录接口
    @apiName GetPlayerScores
    @apiGroup Scores
    @apiParam {Integer} page 页码，可选，默认为1，用于分页查询
    @apiSuccess {Object[]} 返回包含玩家分数记录信息的数组，每个元素包含id、score_value、game_date字段
    @apiError 404 玩家不存在
    """
    player = Player.query.get(player_id)
    if not player:
        app.logger.warning(f"Player with ID {player_id} not found when trying to get player scores.")  # 记录玩家不存在的情况
        return jsonify({"message": "Player not found"}), 404
    page = request.args.get('page', default=1, type=int)  # 获取请求中的页码参数，默认为第1页
    per_page = 10  # 每页显示的记录数，可以根据实际情况调整
    scores_pagination = Score.query.filter_by(player_id=player_id).paginate(page=page, per_page=per_page)
    scores = [{"id": s.id, "score_value": s.score_value, "game_date": s.game_date} for s in scores_pagination.items]
    return jsonify(scores), 200


if __name__ == '__main__':
    # 在应用启动时创建数据库表
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='localhost', port=5000)