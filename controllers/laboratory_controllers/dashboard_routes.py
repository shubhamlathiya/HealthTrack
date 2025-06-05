from flask import render_template

from controllers.laboratory_controllers import laboratory
from middleware.auth_middleware import token_required
from models import UserRole, User
from models.noticeboardModel import Notice
from utils.config import db


@laboratory.route('/dashboard', methods=['GET'])
@token_required(allowed_roles=[UserRole.LABORATORIST.name])
def dashboard(current_user):
    users = User.query.get_or_404(current_user)
    # Get notices for current user based on their role/department
    user_notices = Notice.query.filter(
        Notice.is_active == True,
        Notice.is_deleted == False,
        db.or_(
            db.and_(
                Notice.target_type == 'role',
                Notice.roles.cast(db.String).contains(f'"{users.role.value}"')
            ),
            db.and_(
                Notice.target_type == 'role',
                Notice.roles == None
            )
        )
    ).order_by(
        Notice.priority.desc(),
        Notice.post_date.desc()
    ).all()

    # print(user_notices)
    return render_template("laboratory_templates/dashboard/dashboard.html",
                           notices=user_notices)
