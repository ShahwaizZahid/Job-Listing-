"""Job service layer containing business logic for job operations."""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from database import db
from models import Job


class JobService:
    """Service class for job-related business logic."""

    @staticmethod
    def get_all_jobs(
        search: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        tag: Optional[str] = None,
        sort: str = 'posting_date_desc',
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all jobs with optional filtering, sorting, and pagination.
        
        Returns:
            Tuple of (jobs_list, total_count)
        """
        try:
            # Start with base query
            query = Job.query

            # Apply filters
            filters = []
            
            if search:
                search_filter = or_(
                    Job.title.ilike(f'%{search}%'),
                    Job.company.ilike(f'%{search}%')
                )
                filters.append(search_filter)
            
            if location:
                filters.append(Job.location.ilike(f'%{location}%'))
            
            if job_type:
                filters.append(Job.job_type == job_type)
            
            if tag:
                # Search for tag in comma-separated tags
                filters.append(Job.tags.ilike(f'%{tag}%'))
            
            if filters:
                query = query.filter(and_(*filters))

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if sort == 'posting_date_asc':
                query = query.order_by(asc(Job.posting_date))
            else:  # default to posting_date_desc
                query = query.order_by(desc(Job.posting_date))

            # Apply pagination
            offset = (page - 1) * page_size
            jobs = query.offset(offset).limit(page_size).all()

            # Convert to dictionaries
            jobs_list = [job.to_dict() for job in jobs]

            return jobs_list, total_count

        except SQLAlchemyError as e:
            raise Exception(f"Database error while fetching jobs: {str(e)}")

    @staticmethod
    def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
        """Get a single job by ID."""
        try:
            job = Job.query.get(job_id)
            return job.to_dict() if job else None
        except SQLAlchemyError as e:
            raise Exception(f"Database error while fetching job {job_id}: {str(e)}")

    @staticmethod
    def create_job(job_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, List[str]]]]:
        """
        Create a new job.
        
        Returns:
            Tuple of (job_dict, validation_errors)
        """
        try:
            # Create job instance from data
            job = Job.from_dict(job_data)
            
            # Validate job data
            validation_errors = job.validate()
            if validation_errors:
                return None, validation_errors

            # Check for duplicates (same title, company, location)
            existing_job = Job.query.filter_by(
                title=job.title.strip(),
                company=job.company.strip(),
                location=job.location.strip()
            ).first()
            
            if existing_job:
                return None, {'duplicate': ['Job already exists']}

            # Save to database
            db.session.add(job)
            db.session.commit()
            
            return job.to_dict(), None

        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error while creating job: {str(e)}")

    @staticmethod
    def update_job(job_id: int, job_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, List[str]]]]:
        """
        Update an existing job.
        
        Returns:
            Tuple of (job_dict, validation_errors)
        """
        try:
            # Get existing job
            job = Job.query.get(job_id)
            if not job:
                return None, {'not_found': ['Job not found']}

            # Update fields if provided
            if 'title' in job_data:
                job.title = job_data['title']
            if 'company' in job_data:
                job.company = job_data['company']
            if 'location' in job_data:
                job.location = job_data['location']
            if 'posting_date' in job_data:
                posting_date = job_data['posting_date']
                if isinstance(posting_date, str):
                    try:
                        from datetime import datetime
                        job.posting_date = datetime.fromisoformat(posting_date.replace('Z', '+00:00'))
                    except ValueError:
                        pass  # Invalid date format, leave unchanged
                elif posting_date is not None:
                    job.posting_date = posting_date
            if 'posting_date_raw' in job_data:
                job.posting_date_raw = job_data['posting_date_raw']
            if 'job_type' in job_data:
                job.job_type = job_data['job_type']
            if 'tags' in job_data:
                job.tags = job_data['tags']

            # Validate updated job data
            validation_errors = job.validate()
            if validation_errors:
                return None, validation_errors

            # Save changes
            db.session.commit()
            
            return job.to_dict(), None

        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error while updating job {job_id}: {str(e)}")

    @staticmethod
    def delete_job(job_id: int) -> bool:
        """
        Delete a job by ID.
        
        Returns:
            True if deleted, False if not found
        """
        try:
            job = Job.query.get(job_id)
            if not job:
                return False

            db.session.delete(job)
            db.session.commit()
            
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error while deleting job {job_id}: {str(e)}")

    @staticmethod
    def validate_job_data(job_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate job data without creating a job instance."""
        job = Job.from_dict(job_data)
        return job.validate()

    @staticmethod
    def get_job_types() -> List[str]:
        """Get list of valid job types."""
        return Job.VALID_JOB_TYPES.copy()

    @staticmethod
    def search_jobs_by_tag(tag: str) -> List[Dict[str, Any]]:
        """Search jobs by a specific tag."""
        try:
            jobs = Job.query.filter(Job.tags.ilike(f'%{tag}%')).all()
            return [job.to_dict() for job in jobs]
        except SQLAlchemyError as e:
            raise Exception(f"Database error while searching jobs by tag: {str(e)}")
