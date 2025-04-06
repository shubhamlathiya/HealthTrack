from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import RECORDS_DEATH, RECORDS_BIRTH


@admin.route(RECORDS_DEATH, methods=['GET'], endpoint='records_death')
def records_death():
    return render_template("admin_templates/records/death_records.html")

@admin.route(RECORDS_BIRTH, methods=['GET'], endpoint='records_birth')
def records_birth():
    return render_template("admin_templates/records/birth_records.html")