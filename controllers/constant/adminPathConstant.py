# auth
AUTH = "auth"
LOGIN = "/login"
REGISTER = "/register"
FORGOT_PASSWORD = "/forgot-password"
RESET_PASSWORD = "/reset-password"

# admin
ADMIN = "/admin"

# blood-bank
BLOOD_BANK = "/blood-bank"
BLOOD_BANK_DONOR = f"{BLOOD_BANK}/donor"
BLOOD_BANK_ADD_DONOR = f"{BLOOD_BANK}/add-donor"
BLOOD_BANK_STOCK = f"{BLOOD_BANK}/stock"
BLOOD_BANK_ISSUED = f"{BLOOD_BANK}/issued"

# accounts
ACCOUNTS = "/accounts"
ACCOUNTS_INCOME = f"{ACCOUNTS}/income"
ACCOUNTS_EXPENSES = f"{ACCOUNTS}/expenses"
ACCOUNTS_INVOICES = f"{ACCOUNTS}/invoices"
ACCOUNTS_PAYMENTS = f"{ACCOUNTS}/payments"
ACCOUNTS_CREATE_INVOICE = f"{ACCOUNTS}/create-invoice"
ACCOUNTS_INVOICES_DETAILS = f"{ACCOUNTS}/invoice-details"

# ambulance
AMBULANCE = "/ambulance"
AMBULANCE_ADD_AMBULANCE = f"{AMBULANCE}/add-ambulance"
AMBULANCE_AMBULANCE_LIST = f"{AMBULANCE}/ambulance-list"
AMBULANCE_AMBULANCE_CALL_LIST = f"{AMBULANCE}/ambulance-call-list"
AMBULANCE_ADD_DRIVER = f"{AMBULANCE}/add-driver"
AMBULANCE_DRIVER_LIST = f"{AMBULANCE}/driver-list"

DEPARTMENT = "/department"
DEPARTMENT_LIST = f"{DEPARTMENT}/department-list"
DEPARTMENT_ADD_DEPARTMENT = f"{DEPARTMENT}/add-department"

DOCTOR = "/doctor"
DOCTOR_LIST = f"{DOCTOR}/doctor-list"
DOCTOR_ADD_DOCTOR = f"{DOCTOR}/add-doctor"
DOCTOR_ASSIGN_DEPARTMENT = f"/{DOCTOR}/assign-department"
DOCTOR_UPDATE_ASSIGN_DEPARTMENT = f"{DOCTOR}/update-assign-department"
DOCTOR_SHIFT_MANAGEMENT = f"{DOCTOR}/shift-management"
DOCTOR_UPDATE_SHIFT_MANAGEMENT = f"{DOCTOR}/update-shift-management"

# human-resources
HUMAN_RESOURCES = "/human-resources"
HUMAN_RESOURCES_HR_APPROVALS = f"{HUMAN_RESOURCES}/hr-approvals"
HUMAN_RESOURCES_STAFF_LEAVES = f"{HUMAN_RESOURCES}/staff-leaves"
HUMAN_RESOURCES_STAFF_HOLIDAY = f"{HUMAN_RESOURCES}/staff-holidays"
HUMAN_RESOURCES_STAFF_ATTENDANCE = f"{HUMAN_RESOURCES}/staff-attendance"

# insurance
INSURANCE = "/insurance"
INSURANCE_PATIENT = f"{INSURANCE}/patient"
INSURANCE_PROVIDER = f"{INSURANCE}/provider"
INSURANCE_ADD_INSURANCE_PROVIDER = f"{INSURANCE}/add-insurance-provider"
INSURANCE_CLAIM_STATUS = f"{INSURANCE}/claim-status"

# pharmacy
PHARMACY = "/pharmacy"
PHARMACY_MEDICINE_LIST = f"/{PHARMACY}/medicine-list"
PHARMACY_MEDICINE_ADD = f"{PHARMACY}/add-medicine"
PHARMACY_MEDICINE_EDIT = f"{PHARMACY}/edit-medicine"
PHARMACY_MEDICINE_DELETE = f"{PHARMACY}/delete-medicine"
PHARMACY_MEDICINE_RESTOCK = f"{PHARMACY}/restock-medicine"
PHARMACY_MEDICINE_TRANSACTIONS = f"{PHARMACY}/transactions-medicine"
PHARMACY_MEDICINE_DISPENSE = f"{PHARMACY}/dispense-medicine"
PHARMACY_MEDICINE_RESTORE = f"{PHARMACY}/restore-medicine"

PHARMACY_MEDICINE_CATEGORIES = f"/{PHARMACY}/medicine-categories"
PHARMACY_MEDICINE_ADD_CATEGORIES = f"/{PHARMACY}/add-medicine-categories"
PHARMACY_MEDICINE_EDIT_CATEGORIES = f"{PHARMACY}/edit-medicine-categories"
PHARMACY_MEDICINE_DELETE_CATEGORIES = f"{PHARMACY}/delete-medicine-categories"
PHARMACY_MEDICINE_RESTORE_CATEGORIES = f"{PHARMACY}/restore-medicine-categories"


PHARMACY_MEDICINE_COMPANIES = f"/{PHARMACY}/medicine-companies"
PHARMACY_MEDICINE_ADD_COMPANIES = f"{PHARMACY}/add-medicine-companies"
PHARMACY_MEDICINE_EDIT_COMPANIES = f"{PHARMACY}/edit-medicine-companies"
PHARMACY_MEDICINE_DELETE_COMPANIES = f"{PHARMACY}/delete-medicine-companies"
PHARMACY_MEDICINE_RESTORE_COMPANIES = f"{PHARMACY}/restore-medicine-companies"


# records
RECORDS = "/records"
RECORDS_DEATH = f"/{RECORDS}/death"
RECORDS_ADD_DEATH = f"{RECORDS}/add-death"
RECORDS_DEATH_DELETE = f"{RECORDS}/death-delete"
RECORDS_DEATH_EDIT = f"{RECORDS}/death-edit"
RESTORE_RECORDS_DEATH = f"{RECORDS}/restore-death"
RECORDS_BIRTH = f"/{RECORDS}/birth"
RECORDS_ADD_BIRTH = f"{RECORDS}/add-birth"
RECORDS_BIRTH_DELETE = f"{RECORDS}/birth-delete"
RECORDS_BIRTH_EDIT = f"{RECORDS}/birth-edit"
RECORDS_BIRTH_MEDICAL_VISIT = f"{RECORDS}/birth-visit"
RECORDS_BIRTH_MEDICAL_VISIT_DELETE = f"{RECORDS}/birth-visit-delete"
RESTORE_RECORDS_BIRTH = f"{RECORDS}/restore-birth"
RESTORE_BIRTH_MEDICAL_VISIT = f"{RECORDS}/restore-birth-visit"

# room
ROOM = "/room"
ROOM_ADD_ROOM = f"/{ROOM}/add-room"
ROOM_ADD_BAD = f"/{ROOM}/add-bad"
ROOM_DELETE_BAD = f"{ROOM}/delete-bad"
ROOM_EDIT_ROOM = f"{ROOM}/edit-room"
ROOM_DELETE_ROOM = f"{ROOM}/delete-room"
ROOM_RESTORE_ROOM = f"{ROOM}/restore-room"
ROOM_DISCHARGE_ROOM = f"{ROOM}/discharge-room"
ROOM_CLEANING_LOGS = f"{ROOM}/cleaning-logs"
ROOM_COMPLETE_CLEANING_LOGS = f"{ROOM}/complete-cleaning-logs"
ROOM_AVAILABLE_ROOM = f"{ROOM}/available-room"
ROOM_BOOK_ROOM = f"{ROOM}/book-room"
ROOM_ROOM_STATISTICS = f"{ROOM}/room-statistics"
ROOM_ROOM_ALLOTTED = f"/{ROOM}/rooms-allotted"
ROOM_ROOM_BY_DEPT = f"{ROOM}/rooms-by-dept"

GET_PATIENT = "/get-patient"
GET_ROOM_DEPARTMENT = "/get-room-department"

STAFF = "/staff"
