from flask import render_template

from controllers.admin_controllers import admin


@admin.route('/ambulance/add-ambulance', methods=['GET'], endpoint='add-ambulance')
def addAmbulance():
    return render_template("admin_templates/ambulance/add-ambulance.html")

@admin.route('/ambulance/ambulance-list', methods=['GET'], endpoint='ambulance-list')
def ambulanceList():
    return render_template("admin_templates/ambulance/ambulance-list.html")

@admin.route('/ambulance/ambulance-call-list', methods=['GET'], endpoint='ambulance-call-list')
def ambulanceCallList():
    return render_template("admin_templates/ambulance/ambulance-call-list.html")

@admin.route('/ambulance/add-driver', methods=['GET'], endpoint='add-driver')
def ambulanceAddDriver():
    return render_template("admin_templates/ambulance/add-driver.html")

@admin.route('/ambulance/driver-list', methods=['GET'], endpoint='driver-list')
def ambulanceDriverList():
    return render_template("admin_templates/ambulance/driver-list.html")
