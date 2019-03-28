from flask import Flask, request, url_for, jsonify, json, g
from flask_restful import Api, Resource, reqparse
import sqlite3
import sys
from datetime import datetime
from functools import wraps
from passlib.hash import pbkdf2_sha256

#db_connect = create_engine('sqlite:///blog.db')
DATABASE = '/home/student/github/Blog_Database.db'
app = Flask(__name__)
#api = Api(app)

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

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        username = request.authorization["username"]
        password = request.authorization["password"]
        if check_auth(username, password):
            return f(*args, **kwargs)
        else:
            make_response('Could not verify',401, {'WWW-Authenticate':'Basic realm="Login Required"'})
    return decorated

def check_auth(username, password):
    cur = get_db().cursor()
    cur.execute('SELECT user_name, password FROM users WHERE user_name=?',(username,))
    row = cur.fetchone()
    if row and row[0] == username and pbkdf2_sha256.verify(password, row[1]):
        return True
    else:
        return False

@app.route("/")
def index():
    cur = get_db().cursor()
    cur.execute('SELECT * FROM articles;')
    results = cur.fetchall()
    return '''<h1>{}<h1>'''.format(results)

#curl --include -u kunal:kunal --verbose --request POST --header 'Content-Type: application/json' --data '{"tags":["tag3","tag4"]}' http://localhost:5100/new_tag/1
@app.route('/new_tag/<article_id>', methods = ['POST'])
@auth_required
def api_new_tag(article_id):
    data = None
    articleId = None
    tagData = None
    lastRowId = None
    if request.method == 'POST':
        statusCode:bool = False
        cur = get_db().cursor()
        try:
            data = request.get_json()
            tags = data['tags']
            cur.execute('SELECT article_id FROM articles WHERE article_id = ?',(article_id,))
            isArticleIDpresent = cur.fetchone()
            if isArticleIDpresent != None:
                for tag in tags:
                    cur.execute('SELECT tag_id from tags where tag_name = ?',(tag,))
                    tagData = cur.fetchall()
                    if len(tagData) == 0:
                        cur.execute('INSERT INTO tags (tag_name) VALUES (?)',(tag,))
                        newTagId = cur.lastrowid
                    else:
                        newTagId = tagData[0][0]
                    cur.execute('INSERT INTO article_tags (article_id, tag_id) VALUES (?,?)',(article_id,newTagId))
                    lastRowId = cur.lastrowid
                    get_db().commit()
                if lastRowId != None:
                            statusCode = True
            else:
                statusCode = False
        except:
            get_db().rollback()
            statusCode = False
        finally:
            if statusCode:
                url = 'http://127.0.0.1:5100/tags/' + str(newTagId)
                resp = jsonify(data)
                resp.status_code = 201
                resp.headers['Link'] = url
                return resp
            else:
                return jsonify(message="Failed"),409

#curl -u kunal:kunal --include --verbose --request DELETE --header 'Content-Type: application/json' http://localhost:5100/remove_tags/<article_id>
@app.route('/remove_tags/<article_id>', methods = ['DELETE'])
@auth_required
def api_remove_tags(article_id):
    cur = get_db().cursor()
    status_code :bool= False
    try:
        cur.execute("DELETE FROM article_tags WHERE article_id = ?",(article_id,))
        get_db().commit()
        if cur.rowcount >= 1:
            status_code = True
    except:
        get_db().rollback()
        status_code = False
    finally:
        if status_code:
            return jsonify(message="Tags Deleted successfully"), 200
        else:
            return jsonify(message="Tags Deletion Failed"), 409

#curl -u kunal:kunal --include --verbose --request GET --header 'Content-Type: application/json' http://localhost:5100/get_articles_for_tag/<tag_id>
@app.route('/get_articles_for_tag/<tag_id>', methods = ['GET'])
def api_get_articles_for_tag(tag_id):
    cur = get_db().cursor()
    no_tags_found:bool = False
    status_code:bool = False
    try:
        cur.execute("SELECT url FROM articles WHERE article_id IN (SELECT article_id FROM article_tags WHERE tag_id = ?)",(tag_id,))
        articles = cur.fetchall()
        if len(articles) != 0:
            status_code = True
        else:
            no_tags_found = True
    except:
        get_db().rollback()
        status_code = False
    finally:
        if status_code:
            resp = jsonify(articles)
            resp.status_code = 200
            return resp
        else:
            if no_tags_found == True:
                return jsonify(message="No Articles Found"), 404
            else:
                return jsonify(message="Failed"), 409

#curl -u kunal:kunal --include --verbose --request GET --header 'Content-Type: application/json' http://localhost:5100/get_tags/<article_id>
@app.route('/get_tags/<article_id>', methods = ['GET'])
def api_get_tags(article_id):
    cur = get_db().cursor()
    no_tags_found = False
    status_code = False
    try:
        cur.execute('SELECT article_id FROM articles WHERE article_id = ?',(article_id,))
        isArticleIDpresent = cur.fetchone()
        if isArticleIDpresent != None:
            cur.execute("SELECT tag_name FROM tags WHERE tag_id IN (SELECT tag_id FROM article_tags WHERE article_id =?)",(article_id,))
            tags = cur.fetchall()
            if len(tags) != 0:
                status_code = True
            else:
                no_tags_found = True
        else:
            status_code = False
    except:
        get_db().rollback()
        status_code = False
    finally:
        if status_code:
            resp = jsonify(tags)
            resp.status_code = 200
            return resp
        else:
            if no_tags_found == True:
                return jsonify(message="No Tags Found"), 404
            else:
                return jsonify(message="Failed"), 404

@app.errorhandler(404)
def not_found(error=None):
    message = {
    'status' : 404,
    'message': 'Not found : '+ request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return 404

if __name__ == '__main__':
    app.run(debug=True,port=5100)
#class Article(Resource):
#    def get(self, name):
#        conn = db_conneect .connnect()
#        for article in articles:
#            if(name == user["name"]):
#                return article, 200
#        return "Article not found, 404
