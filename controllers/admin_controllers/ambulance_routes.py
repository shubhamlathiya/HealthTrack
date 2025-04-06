from flask import render_template

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import AMBULANCE_ADD_AMBULANCE, AMBULANCE_AMBULANCE_LIST, \
    AMBULANCE_AMBULANCE_CALL_LIST, AMBULANCE_ADD_DRIVER, AMBULANCE_DRIVER_LIST


@admin.route(AMBULANCE_ADD_AMBULANCE, methods=['GET'], endpoint='add-ambulance')
def addAmbulance():
    return render_template("admin_templates/ambulance/add-ambulance.html")

@admin.route(AMBULANCE_AMBULANCE_LIST, methods=['GET'], endpoint='ambulance-list')
def ambulanceList():
    return render_template("admin_templates/ambulance/ambulance-list.html")

@admin.route(AMBULANCE_AMBULANCE_CALL_LIST, methods=['GET'], endpoint='ambulance-call-list')
def ambulanceCallList():
    return render_template("admin_templates/ambulance/ambulance-call-list.html")

@admin.route(AMBULANCE_ADD_DRIVER, methods=['GET'], endpoint='add-driver')
def ambulanceAddDriver():
    return render_template("admin_templates/ambulance/add-driver.html")

@admin.route(AMBULANCE_DRIVER_LIST, methods=['GET'], endpoint='driver-list')
def ambulanceDriverList():
    return render_template("admin_templates/ambulance/driver-list.html")
