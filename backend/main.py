
import os
# from flask import Flask, jsonify
from flask import Flask
from flask_cors import CORS
# from config import config
# from database import init_db
# from routes.jobs import jobs_bp
# from routes.jobs import jobs_routes
from routes.jobs import jobs_routes
from flask_sqlalchemy import SQLAlchemy
from database import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/jobboard'
db.init_app(app)

CORS(app)


app.register_blueprint(jobs_routes) 

@app.route("/", methods=["GET"])
def hello():
    return {"message": "Hello, Python!"}

if __name__ == "__main__":
    app.run(debug=True, port=5000)


