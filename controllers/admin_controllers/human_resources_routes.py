from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import HUMAN_RESOURCES_HR_APPROVALS, HUMAN_RESOURCES_STAFF_LEAVES, \
    HUMAN_RESOURCES_STAFF_HOLIDAY, HUMAN_RESOURCES_STAFF_ATTENDANCE


@admin.route(HUMAN_RESOURCES_HR_APPROVALS, methods=['GET'], endpoint='hr-approvals')
def human_resources_hr():
    return render_template("admin_templates/human_resources/hr-approvals.html")


@admin.route(HUMAN_RESOURCES_STAFF_LEAVES, methods=['GET'], endpoint='staff-leaves')
def human_resources_staff():
    return render_template("admin_templates/human_resources/staff-leaves.html")


@admin.route(HUMAN_RESOURCES_STAFF_HOLIDAY, methods=['GET'], endpoint='staff-holidays')
def human_resources_staff_holidays():
    return render_template("admin_templates/human_resources/staff-holidays.html")


@admin.route(HUMAN_RESOURCES_STAFF_ATTENDANCE, methods=['GET'], endpoint='staff-attendance')
def human_resources_staff_attendance():
    return render_template("admin_templates/human_resources/staff-attendance.html")