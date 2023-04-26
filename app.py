from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin 
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow 
from sqlalchemy.orm import relationship
from flask_bcrypt import Bcrypt
import logging
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__)) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
CORS(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)

logging.getLogger('flask_cors').level = logging.DEBUG



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    tasks = db.relationship('Tasks', backref='user', cascade="all, delete, delete-orphan")

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __init__(self, task, user_id):
        self.task = task
        self.user_id = user_id

class TasksSchema(ma.Schema):
    class Meta:
        fields = ('id',"task", "user_id")

tasks_schema = TasksSchema()
multiple_tasks_schema = TasksSchema(many=True)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'password','tasks')
    tasks = ma.Nested(multiple_tasks_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)



@app.route('/user/add', methods=['POST'])
def add_user():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    username_duplicate = db.session.query(User).filter(User.username == username).first()

    if username_duplicate is not None:
        return jsonify("Error: The username is already registered.")

    encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username, encrypted_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'username': new_user.username})


@app.route('/users/login', methods=['POST'])
def login():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')
    
    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    
    user = db.session.query(User).filter(User.username == username).first()
    
    if user is None:
        response = jsonify("user NONE EXISTENT")
        return set_headers_post(response)
    elif bcrypt.check_password_hash(user.password, password) == False:
        response = jsonify("PASSWORD WRONG TRY AGAIN")
        return set_headers_post(response)
    else:
        user_found = False
        admin_logged_in = False
        if username == 'Roderick' and password == "Nova":
            admin_logged_in = True
            user_found = True
        if user :
            user_found = True
        elif bcrypt.check_password_hash(user.password, password) == False: 
            user_found = False
            response = jsonify("PASSWORD WRONG TRY AGAIN")
            return set_headers_post(response)
        response = jsonify({'data': user_schema.dump(user), 'admin_logged_in': admin_logged_in, 'user_found': user_found})
        return set_headers_post(response)



@app.route('/user/verify', methods=['POST'])
def verify_user():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    user = db.session.query(User).filter(User.username == username).first()

    if user is None:
        return jsonify("User NOT verified")

    if bcrypt.check_password_hash(user.password, password) == False:
        return jsonify("User NOT verified")

    return jsonify(user_schema.dump(user))


@app.route('/user/get', methods=['GET'])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(all_users))

@app.route('/user/get/<id>', methods=['GET'])
def get_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))

@app.route('/user/delete/<id>', methods=['DELETE'])
def delete_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    db.session.delete(user)
    db.session.commit()



    return jsonify("The user has been deleted")

@app.route("/tasks/add", methods=["POST"])
def add_task():
    if request.content_type != "application/json":
        return jsonify("Error Please send as JSON")
    
    post_data = request.get_json()
    task = post_data.get("task")
    user_id = post_data.get("user_id")

    new_task = Tasks(task, user_id)
    print("tasked recieved", new_task)

    db.session.add(new_task)
    db.session.commit()

    return jsonify(tasks_schema.dump(new_task))

@app.route('/tasks/getall/<user_id>', methods=["GET"])
def get_tasks(user_id):

    

    all_tasks = db.session.query(Tasks).filter(Tasks.user_id == user_id).all()
    return jsonify(multiple_tasks_schema.dump(all_tasks))



@app.route("/tasks/delete/<id>", methods=["DELETE"])
@cross_origin()
def delete_task(id):
    
    logging.debug(id)
    task = db.session.query(Tasks).filter(Tasks.id == id).first()
#    something different for commit
    
    db.session.delete(task)
    db.session.commit()
    return "The task has been deleted."




if __name__ == '__main__':
    app.run(debug=True)
