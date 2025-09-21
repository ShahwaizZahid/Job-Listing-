from datetime import datetime
from flask import jsonify, request

from models import Job
from database import db

def get_jobs_controller():
    try:
        # Query parameters
        search = request.args.get("search", type=str)
        location = request.args.get("location", type=str)
        job_type = request.args.get("job_type", type=str)
        tag = request.args.get("tag", type=str)
        sort = request.args.get("sort", default="posting_date_desc", type=str)
        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=10, type=int)

        # Enforce max page size
        if page_size > 100:
            page_size = 100

        # Base query
        query = Job.query

        # Apply filters
        if search:
            query = query.filter(
                (Job.title.ilike(f"%{search}%")) | (Job.company.ilike(f"%{search}%"))
            )
        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))
        if job_type:
            query = query.filter(Job.job_type == job_type)
        if tag:
            query = query.filter(Job.tags.ilike(f"%{tag}%"))

        # Sorting
        if sort == "posting_date_asc":
            query = query.order_by(Job.posting_date.asc())
        else:  # default newest first
            query = query.order_by(Job.posting_date.desc())

        # Pagination
        total = query.count()
        jobs = query.offset((page - 1) * page_size).limit(page_size).all()

        # Response
        job_list = []
        for job in jobs:
            job_list.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "posting_date": job.posting_date.isoformat() if job.posting_date else None,
                "posting_date_raw": job.posting_date_raw,
                "job_type": job.job_type,
                "tags": job.tags,
            })

        return jsonify({
            "jobs": job_list,
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def create_job_controller():
    data = request.get_json()

    # Validation errors storage
    errors = {}

    # Required fields
    if not data.get("title") or not data["title"].strip():
        errors["title"] = "required"
    if not data.get("company") or not data["company"].strip():
        errors["company"] = "required"
    if not data.get("location") or not data["location"].strip():
        errors["location"] = "required"

    # posting_date validation
    posting_date = None
    if data.get("posting_date"):
        try:
            posting_date = datetime.fromisoformat(data["posting_date"].replace("Z", "+00:00"))
        except ValueError:
            errors["posting_date"] = "must be valid ISO datetime"

    # job_type validation
    allowed_types = ["Full-time", "Part-time", "Contract", "Internship"]
    if data.get("job_type") and data["job_type"] not in allowed_types:
        errors["job_type"] = f"must be one of {allowed_types}"

    # Return validation errors
    if errors:
        return jsonify({"error": "Validation failed", "fields": errors}), 400

    # Duplicate check (same title + company + location)
    existing = Job.query.filter_by(
        title=data["title"],
        company=data["company"],
        location=data["location"]
    ).first()

    if existing:
        return jsonify({"error": "Job already exists"}), 409

    # Create job object
    new_job = Job(
        title=data["title"],
        company=data["company"],
        location=data["location"],
        posting_date=posting_date,
        posting_date_raw=data.get("posting_date_raw"),
        job_type=data.get("job_type"),
        tags=data.get("tags")
    )

    db.session.add(new_job)
    db.session.commit()

    # Response
    return jsonify({
        "id": new_job.id,
        "title": new_job.title,
        "company": new_job.company,
        "posting_date": new_job.posting_date.isoformat() if new_job.posting_date else None,
        "posting_date_raw": new_job.posting_date_raw,
        "job_type": new_job.job_type,
        "tags": new_job.tags
    }), 201



def get_specfic_job_controller(job_id):
    job = Job.query.get(job_id)  # Fetch by primary key
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify({
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "posting_date": job.posting_date.isoformat() if job.posting_date else None,
        "posting_date_raw": job.posting_date_raw,
        "job_type": job.job_type,
        "tags": job.tags
    }), 200



def update_job_controller(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    data = request.get_json()
    if not data or len(data) == 0:
        return jsonify({"error": "Validation failed", "fields": "At least one field required"}), 400

    # Allowed job types
    allowed_job_types = ["Full-time", "Part-time", "Contract", "Internship"]

    # Update fields if provided
    if "title" in data:
        if not data["title"].strip():
            return jsonify({"error": "Validation failed", "fields": {"title": "required"}}), 400
        job.title = data["title"]

    if "company" in data:
        if not data["company"].strip():
            return jsonify({"error": "Validation failed", "fields": {"company": "required"}}), 400
        job.company = data["company"]

    if "location" in data:
        if not data["location"].strip():
            return jsonify({"error": "Validation failed", "fields": {"location": "required"}}), 400
        job.location = data["location"]

    if "posting_date" in data:
        try:
            job.posting_date = datetime.fromisoformat(data["posting_date"].replace("Z", "+00:00"))
        except Exception:
            return jsonify({"error": "Validation failed", "fields": {"posting_date": "Invalid ISO datetime"}}), 400

    if "posting_date_raw" in data:
        job.posting_date_raw = data["posting_date_raw"]

    if "job_type" in data:
        if data["job_type"] not in allowed_job_types:
            return jsonify({"error": "Validation failed", "fields": {"job_type": "Invalid type"}}), 400
        job.job_type = data["job_type"]

    if "tags" in data:
        job.tags = data["tags"]

    # Auto update timestamp
    job.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "posting_date": job.posting_date.isoformat() if job.posting_date else None,
        "posting_date_raw": job.posting_date_raw,
        "job_type": job.job_type,
        "tags": job.tags
    }), 200    