from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/human-resources/hr-approvals', methods=['GET'], endpoint='hr-approvals')
def human_resources_hr():
    return render_template("admin_templates/human_resources/hr-approvals.html")


@admin.route('/human-resources/staff-leaves', methods=['GET'], endpoint='staff-leaves')
def human_resources_staff():
    return render_template("admin_templates/human_resources/staff-leaves.html")


@admin.route('/human-resources/staff-holidays', methods=['GET'], endpoint='staff-holidays')
def human_resources_staff_holidays():
    return render_template("admin_templates/human_resources/staff-holidays.html")


@admin.route('/human-resources/staff-attendance', methods=['GET'], endpoint='staff-attendance')
def human_resources_staff_attendance():
    return render_template("admin_templates/human_resources/staff-attendance.html")