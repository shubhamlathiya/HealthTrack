from datetime import datetime

from sqlalchemy.dialects.mysql import JSON

from utils.config import db


class Notice(db.Model):
    __tablename__ = 'notices'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)
    priority = db.Column(db.Enum('high', 'medium', 'low', name='priority_enum'),
                         default='medium', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    attachment = db.Column(db.String(255))
    target_type = db.Column(db.Enum('role', 'department', name='target_type_enum'),
                            nullable=False)

    # Relationships
    poster = db.relationship('User', backref='notices')
    departments = db.relationship('Department', secondary='notice_departments',
                                  backref='notices', lazy='dynamic')

    # For role-based notices
    roles = db.Column(JSON)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Notice {self.id}: {self.title}>'

    def get_target_display(self):
        if self.target_type == 'role':
            return ', '.join(self.roles) if self.roles else 'All Roles'
        return ', '.join([dept.name for dept in self.departments]) if self.departments else 'All Departments'


class NoticeDepartments(db.Model):
    __tablename__ = 'notice_departments'
    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id', ondelete='CASCADE'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'))
