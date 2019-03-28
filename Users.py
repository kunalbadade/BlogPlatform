from flask import Flask, request, url_for, jsonify, json, g, make_response
from functools import wraps
from passlib.hash import pbkdf2_sha256
import sqlite3

DATABASE = '/home/student/github/Blog_Database.db'
app = Flask(__name__)

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if(request.authorization != None and request.authorization["username"] != None and request.authorization["password"] != None):
            username = request.authorization["username"]
            password = request.authorization["password"]
        else:
            return make_response('User does not exists.\n' 'Please provide user credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        if check_auth(username, password):
            return f(*args, **kwargs)
        else:
            return  make_response('Could not verify the credentials.\n' 'Please use correct credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated

def check_auth(username, password):
    cur = get_db().cursor().execute("SELECT user_name, password from users WHERE user_name=?", (username,))
    row = cur.fetchone()
    if row and row[0] == username and pbkdf2_sha256.verify(password, row[1]):
        return True
    else:
        return False

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def api_root():
    return "Welcome"

#curl --include --verbose --request POST --header 'Content-Type: application/json' --data '{"user_name" : "parag", "password" : "parag"}' http://localhost:5200/create_user
@app.route('/create_user', methods = ['POST'])
def api_create_user():
    if request.method == 'POST':
        status_code:bool = False
        cur = get_db().cursor()
        userdata = request.get_json()
        number_of_rows = None
        try:
            cur.execute("SELECT COUNT(*) FROM users WHERE user_name = ?", (userdata['user_name'],))
            row = cur.fetchone()
            number_of_rows=row[0]
            if number_of_rows <= 0:
                hashed_password = pbkdf2_sha256.hash(userdata['password'])
                cur.execute("INSERT INTO users (user_name, password, active_status) VALUES (?, ?, ?)",(userdata['user_name'], hashed_password, 1))
                status_code = True
                get_db().commit()
        except:
            get_db().rollback()
            status_code = False
        finally:
            if status_code:
                return jsonify(message="User Created successfully"), 201
            else:
                return jsonify(message="User Already Exists"), 409

#curl -u parag:parag --include --verbose --request DELETE --header 'Content-Type: application/json' http://localhost:5200/delete_user
@app.route('/delete_user', methods=['DELETE'])
@auth_required
def api_delete_user():
        if request.method == 'DELETE':
            status_code:bool = False
        cur = get_db().cursor()
        username = request.authorization["username"]
        try:
            cur.execute("UPDATE users SET active_status =? WHERE user_name=?",(0, username,))
            if(cur.rowcount >= 1):
                get_db().commit()
                status_code = True
        except:
            get_db().rollback()
            status_code = False
        finally:
            if status_code:
                return jsonify(message="User deleted successfully"), 201
            else:
                return jsonify(message="Failed to delete the user"), 409

#curl -u shekhar:palit -i --request PATCH --header 'Content-Type: application/json' --data '{"user_name" : "shekhar","old_password" : "palit", "password" : "palit1234"}' http://localhost:5200/change_password
@app.route('/change_password', methods=['PATCH'])
@auth_required
def api_change_password():
    if request.method == 'PATCH':
        status_code:bool = False
    cur = get_db().cursor()
    try:
        userdata = request.get_json()
        cur.execute("select password from users where user_name = ?", (userdata['user_name'],))
        row = cur.fetchone()
        if pbkdf2_sha256.verify(userdata['old_password'], row[0]):
            new_hashed_password = pbkdf2_sha256.hash(userdata['password'])
            cur.execute("UPDATE users SET password=? WHERE user_name=? AND EXISTS(SELECT 1 FROM users WHERE user_name=? AND active_status=1)", (new_hashed_password, userdata['user_name'],userdata['user_name'],))
            if(cur.rowcount >=1):
                status_code = True
                get_db().commit()
    except:
        get_db().rollback()
        status_code = False
    finally:
        if status_code:
            return jsonify(message="Password Updated SucessFully"), 200
        else:
            return jsonify(message="Failed to Update the Password"), 409

if __name__ == '__main__':
    app.run(debug=True, port=5200)
