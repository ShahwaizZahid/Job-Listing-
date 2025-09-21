"""Database models for the job board application."""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Text, func
from database import db


class Job(db.Model):
    """Job model representing a job posting."""

    __tablename__ = "jobs"

    # Valid job types
    VALID_JOB_TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship']

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)

    posting_date = Column(DateTime, nullable=True)          # parsed datetime
    posting_date_raw = Column(String(128), nullable=True)   # e.g. "2 days ago"
    job_type = Column(String(64), nullable=True)            # e.g. Full-time
    tags = Column(Text, nullable=True)                      # comma-separated tags

    created_at = Column(DateTime, server_default=func.now())       # auto now
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())                       # auto update

    def __repr__(self) -> str:
        """String representation of Job."""
        return f'<Job {self.id}: {self.title} at {self.company}>'

    def to_dict(self) -> Dict[str, Any]:
        """Convert job instance to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'posting_date': self.posting_date.isoformat() if self.posting_date else None,
            'posting_date_raw': self.posting_date_raw,
            'job_type': self.job_type,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create Job instance from dictionary."""
        job = cls()
        job.title = data.get('title')
        job.company = data.get('company')
        job.location = data.get('location')
        job.posting_date_raw = data.get('posting_date_raw')
        job.job_type = data.get('job_type')
        job.tags = data.get('tags')

        # Handle posting_date
        posting_date = data.get('posting_date')
        if posting_date:
            if isinstance(posting_date, str):
                try:
                    job.posting_date = datetime.fromisoformat(posting_date.replace('Z', '+00:00'))
                except ValueError:
                    pass  # Invalid date format, leave as None
            elif isinstance(posting_date, datetime):
                job.posting_date = posting_date

        return job

    def validate(self) -> Dict[str, List[str]]:
        """Validate job data and return errors."""
        errors = {}

        # Required fields validation
        if not self.title or not self.title.strip():
            errors.setdefault('title', []).append('Title is required')
        elif len(self.title.strip()) > 255:
            errors.setdefault('title', []).append('Title must be 255 characters or less')

        if not self.company or not self.company.strip():
            errors.setdefault('company', []).append('Company is required')
        elif len(self.company.strip()) > 255:
            errors.setdefault('company', []).append('Company must be 255 characters or less')

        if not self.location or not self.location.strip():
            errors.setdefault('location', []).append('Location is required')
        elif len(self.location.strip()) > 255:
            errors.setdefault('location', []).append('Location must be 255 characters or less')

        # Job type validation
        if self.job_type and self.job_type not in self.VALID_JOB_TYPES:
            errors.setdefault('job_type', []).append(
                f'Job type must be one of: {", ".join(self.VALID_JOB_TYPES)}'
            )

        # Tags validation (optional but if provided, should be reasonable)
        if self.tags and len(self.tags) > 1000:
            errors.setdefault('tags', []).append('Tags must be 1000 characters or less')

        # Posting date raw validation
        if self.posting_date_raw and len(self.posting_date_raw) > 128:
            errors.setdefault('posting_date_raw', []).append(
                'Posting date raw must be 128 characters or less'
            )

        return errors

    def is_valid(self) -> bool:
        """Check if job data is valid."""
        return len(self.validate()) == 0

    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def set_tags_from_list(self, tags_list: List[str]) -> None:
        """Set tags from a list."""
        if not tags_list:
            self.tags = None
        else:
            # Clean and filter tags
            clean_tags = [tag.strip() for tag in tags_list if tag.strip()]
            self.tags = ','.join(clean_tags) if clean_tags else None

    def matches_search(self, search_term: str) -> bool:
        """Check if job matches search term in title or company."""
        if not search_term:
            return True

        search_lower = search_term.lower()
        return (
            search_lower in self.title.lower() or
            search_lower in self.company.lower()
        )

    def matches_location(self, location_term: str) -> bool:
        """Check if job matches location term."""
        if not location_term:
            return True

        return location_term.lower() in self.location.lower()

    def has_tag(self, tag: str) -> bool:
        """Check if job has a specific tag."""
        if not tag or not self.tags:
            return False

        tags_list = self.get_tags_list()
        return tag.lower() in [t.lower() for t in tags_list]
