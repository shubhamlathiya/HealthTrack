PATIENT = "/patient"

PATIENT_DASHBOARD = f"{PATIENT}/dashboard"

PATIENT_BLOOD_REQUEST = "/blood-request"
PATIENT_MY_REQUESTS = "/my-blood-requests"
PATIENT_PAY_REQUEST = "/pay-request/<string:request_id>"

PAYMENT_CONFIRMATION = '/payment-confirmation/<string:request_id>'

# appointment
APPOINTMENT = f"/appointment"
VIEW_APPOINTMENT = f"{APPOINTMENT}/view-appointment"
BOOK_APPOINTMENT = f"{APPOINTMENT}/book-appointment"
RESCHEDULE_APPOINTMENT = f"{APPOINTMENT}/reschedule-appointment"
CANCEL_APPOINTMENT = f"{APPOINTMENT}/cancel-appointment"

# prescriptions
PRESCRIPTIONS = "/prescriptions"
VIEW_PRESCRIPTIONS = f"{PRESCRIPTIONS}/view-prescriptions"
SEND_PRESCRIPTION_EMAIL = f"{PRESCRIPTIONS}/send-prescription-email"

PATIENT_AMBULANCE_CALLS = '/ambulance-calls'
PATIENT_AMBULANCE_REQUESTS = '/ambulance-requests'
PATIENT_AMBULANCE_REQUEST_NEW = '/ambulance-request/new'
PATIENT_AMBULANCE_REQUEST_VIEW = '/ambulance-request/view'  # For a single request detail
