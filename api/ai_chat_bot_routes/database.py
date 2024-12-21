from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.hospital

def fetch_appointment():
    appointment = db.appointments.find_one({"patient_id": "P123"})
    return f"Your next appointment is on {appointment['date']} at {appointment['time']}."

def fetch_reports(patient_id):
    reports = db.reports.find({"patient_id": patient_id})
    return [{"name": report['name'], "link": report['file_path']} for report in reports]
