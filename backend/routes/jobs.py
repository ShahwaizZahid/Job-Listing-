from datetime import datetime
from flask import Blueprint, jsonify, request
from models import Job
from controllers.job_controller import create_job_controller, get_jobs_controller, get_specfic_job_controller, update_job_controller
from database import db

jobs_routes = Blueprint('jobs_routes', __name__)

@jobs_routes.route('/jobs', methods=['GET'])
def get_jobs():
    return get_jobs_controller()

