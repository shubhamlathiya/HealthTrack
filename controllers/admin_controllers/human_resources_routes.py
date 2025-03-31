from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/human-resources/hr-approvals', methods=['GET'], endpoint='hr-approvals')
def dashboard():
    return render_template("admin_templates/human_resources/hr-approvals.html")


@admin.route('/human-resources/staff-leaves', methods=['GET'], endpoint='staff-leaves')
def dashboard():
    return render_template("admin_templates/human_resources/staff-leaves.html")


@admin.route('/human-resources/staff-holidays', methods=['GET'], endpoint='staff-holidays')
def dashboard():
    return render_template("admin_templates/human_resources/staff-holidays.html")


@admin.route('/human-resources/staff-attendance', methods=['GET'], endpoint='staff-attendance')
def dashboard():
    return render_template("admin_templates/human_resources/staff-attendance.html")