# admin
ADMIN = "/admin"

ADMIN_DASHBOARD = f"{ADMIN}/dashboard"

# blood-bank
BLOOD_BANK = "/blood-bank"
BLOOD_BANK_DONOR = f"{BLOOD_BANK}/donor"
BLOOD_BANK_ADD_DONOR = f"{BLOOD_BANK}/add-donor"
BLOOD_BANK_EDIT_DONOR = f"{BLOOD_BANK}/edit-donor"
BLOOD_BANK_DELETE_DONOR = f"{BLOOD_BANK}/delete-donor"
BLOOD_BANK_RESTORE_DONOR = f"{BLOOD_BANK}/restore-donor"

BLOOD_BANK_INVENTORY = f'{BLOOD_BANK}/inventory'
BLOOD_BANK_ADD_INVENTORY = f'{BLOOD_BANK}/inventory/add'
BLOOD_BANK_EDIT_INVENTORY = f'{BLOOD_BANK}/inventory/edit'
BLOOD_BANK_DELETE_INVENTORY = f'{BLOOD_BANK}/inventory/delete'
BLOOD_BANK_RESTORE_INVENTORY = f'{BLOOD_BANK}/inventory/restore'

BLOOD_BANK_STOCK = f"{BLOOD_BANK}/stock"
BLOOD_BANK_ADD_STOCK = f"{BLOOD_BANK}/add-stock"
BLOOD_BANK_EDIT_STOCK = f"{BLOOD_BANK}/edit-stock"
BLOOD_BANK_DELETE_STOCK = f"{BLOOD_BANK}/delete-stock"
BLOOD_BANK_RESTORE_STOCK = f"{BLOOD_BANK}/restore-stock"

BLOOD_BANK_ISSUED = f"{BLOOD_BANK}/issued"
BLOOD_BANK_ADD_ISSUED = f"{BLOOD_BANK}/add-issued"
BLOOD_BANK_EDIT_ISSUED = f"{BLOOD_BANK}/edit-issued"
BLOOD_BANK_DELETE_ISSUED = f"{BLOOD_BANK}/delete-issued"
BLOOD_BANK_RESTORE_ISSUED = f"{BLOOD_BANK}/restore-issued"

# Blood Request Routes
BLOOD_BANK_REQUESTS = '/blood-bank/requests'
BLOOD_BANK_ADD_REQUEST = '/blood-bank/requests/add'
BLOOD_BANK_EDIT_REQUEST = '/blood-bank/requests/edit'
BLOOD_BANK_DELETE_REQUEST = '/blood-bank/requests/delete'
BLOOD_BANK_APPROVE_REQUEST = '/blood-bank/requests/approve'
BLOOD_BANK_REJECT_REQUEST = '/blood-bank/requests/reject'
BLOOD_BANK_COMPLETE_REQUEST = '/blood-bank/requests/complete'

# Blood Transfusion Routes
BLOOD_BANK_TRANSFUSIONS = '/blood-bank/transfusions'
BLOOD_BANK_ADD_TRANSFUSION = '/blood-bank/transfusions/add'
BLOOD_BANK_EDIT_TRANSFUSION = '/blood-bank/transfusions/edit'
BLOOD_BANK_DELETE_TRANSFUSION = '/blood-bank/transfusions/delete'

# inventory
INVENTORY = "/inventory"
INVENTORY_ITEM_STOCK_LIST = f"{INVENTORY}/item-stock-list"
INVENTORY_ADD_ITEM = f"{INVENTORY}/add-item"
INVENTORY_EDIT_ITEM = f"{INVENTORY}/edit-item"
INVENTORY_DELETE_ITEM = f"{INVENTORY}/delete-item"
INVENTORY_RESTORE_ITEM = f"{INVENTORY}/restore-item"

INVENTORY_ISSUED_ITEM = f"{INVENTORY}/issued-item"
INVENTORY_ADD_ISSUED_ITEM = f"{INVENTORY}/add-issued-item"
INVENTORY_EDIT_ISSUED_ITEM = f"{INVENTORY}/edit-issued-item"
INVENTORY_DELETE_ISSUED_ITEM = f"{INVENTORY}/delete-issued-item"
INVENTORY_RESTORE_ISSUED_ITEM = f"{INVENTORY}/restore-issued-item"
INVENTORY_RETURN_ISSUED_ITEM = f"{INVENTORY}/return-issued-item"

INVENTORY_ITEM_REQUESTS = f"{INVENTORY}/requests"
INVENTORY_APPROVE_REQUEST = f"{INVENTORY}/approve-request"
INVENTORY_REJECT_REQUEST = f"{INVENTORY}/reject-request"

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
AMBULANCE_AMBULANCE_LIST = f"{AMBULANCE}/ambulance-list"
AMBULANCE_ADD_AMBULANCE = f"{AMBULANCE}/add-ambulance"
AMBULANCE_EDIT_AMBULANCE = f"{AMBULANCE}/edit-ambulance"
AMBULANCE_DELETE_AMBULANCE = f"{AMBULANCE}/delete-ambulance"
AMBULANCE_RESTORE_AMBULANCE = f"{AMBULANCE}/restore-ambulance"
AMBULANCE_TOGGLE_STATUS_AMBULANCE = f"{AMBULANCE}/toggle-status-ambulance"

# driver
AMBULANCE_DRIVER_LIST = f"{AMBULANCE}/driver-list"
AMBULANCE_ADD_DRIVER = f"{AMBULANCE}/add-driver"
AMBULANCE_EDIT_DRIVER = f"{AMBULANCE}/edit-driver"
AMBULANCE_DELETE_DRIVER = f"{AMBULANCE}/delete-driver"
AMBULANCE_RESTORE_DRIVER = f"{AMBULANCE}/restore-driver"
AMBULANCE_TOGGLE_STATUS_DRIVER = f"{AMBULANCE}/toggle-status-driver"

# ambulance-call-list
AMBULANCE_AMBULANCE_CALL_LIST = f"{AMBULANCE}/ambulance-call-list"
AMBULANCE_AMBULANCE_ADD_CALL = f"{AMBULANCE}/add-call"
AMBULANCE_AMBULANCE_EDIT_CALL = f"{AMBULANCE}/edit-call"
AMBULANCE_AMBULANCE_DELETE_CALL = f"{AMBULANCE}/delete-call"
AMBULANCE_AMBULANCE_RESTORE_CALL = f"{AMBULANCE}/restore-call"
AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL = f"{AMBULANCE}/update-status-call"

# department
DEPARTMENT = "/department"
DEPARTMENT_LIST = f"/{DEPARTMENT}/department-list"
DEPARTMENT_ADD_DEPARTMENT = f"{DEPARTMENT}/add-department"
DEPARTMENT_EDIT_DEPARTMENT = f"{DEPARTMENT}/edit-department"
DEPARTMENT_DELETE_DEPARTMENT = f"{DEPARTMENT}/delete-department"
DEPARTMENT_RESTORE_DEPARTMENT = f"{DEPARTMENT}/restore-department"

DEPARTMENT_MANAGE_HEADS = f"/{DEPARTMENT}/manage-heads"
DEPARTMENT_ADD_HEAD = f"/{DEPARTMENT}/add-head"
DEPARTMENT_REMOVE_HEAD = f"/{DEPARTMENT}/remove-head"

# doctor
DOCTOR = "/doctor"
DOCTOR_LIST = f"{DOCTOR}/doctor-list"
DOCTOR_ADD_DOCTOR = f"{DOCTOR}/add-doctor"
DOCTOR_ASSIGN_DEPARTMENT = f"/{DOCTOR}/assign-department"
DOCTOR_UPDATE_ASSIGN_DEPARTMENT = f"{DOCTOR}/update-assign-department"
DOCTOR_REMOVE_ASSIGN_DEPARTMENT = f"{DOCTOR}/remove-assign-department"
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
INSURANCE_CONVERAGE_TYPE = f"/{INSURANCE}/coverage-types"
INSURANCE_ADD_CONVERAGE_TYPE = f"{INSURANCE}/add-coverage-type"
INSURANCE_EDIT_CONVERAGE_TYPE = f"{INSURANCE}/edit-coverage-type"
INSURANCE_DELETE_CONVERAGE_TYPE = f"{INSURANCE}/delete-coverage-type"
INSURANCE_RESTORE_CONVERAGE_TYPE = f"{INSURANCE}/restore-coverage-type"

INSURANCE_PATIENT = f"{INSURANCE}/patient"
INSURANCE_PATIENT_ADD_RECORDS = f"{INSURANCE_PATIENT}/add-records"
INSURANCE_PATIENT_EDIT_RECORDS = f"{INSURANCE_PATIENT}/edit-records"
INSURANCE_PATIENT_DELETE_RECORDS = f"{INSURANCE_PATIENT}/delete-records"
INSURANCE_PATIENT_RESTORE_RECORDS = f"{INSURANCE_PATIENT}/restore-records"

INSURANCE_PROVIDER = f"/{INSURANCE}/provider"
INSURANCE_ADD_INSURANCE_PROVIDER = f"{INSURANCE}/add-insurance-provider"
INSURANCE_EDIT_INSURANCE_PROVIDER = f"{INSURANCE}/edit-insurance-provider"
INSURANCE_DELETE_INSURANCE_PROVIDER = f"{INSURANCE}/delete-insurance-provider"
INSURANCE_RESTORE_INSURANCE_PROVIDER = f"{INSURANCE}/restore-insurance-provider"

INSURANCE_CLAIM_STATUS = f"{INSURANCE}/claim-status"
INSURANCE_NEW_CLAIM = f"{INSURANCE}/new-claim"
INSURANCE_CLAIM_STATUS_EDIT = f"{INSURANCE}/edit-claim-status"
INSURANCE_CLAIM_STATUS_DELETE = f"{INSURANCE}/delete-claim-status"
INSURANCE_CLAIM_STATUS_RESTORE = f"{INSURANCE}/restore-claim-status"

INSURANCE_CLAIM_STATUS_PROCESS = f"{INSURANCE}/claim-status-process"
INSURANCE_CLAIM_STATUS_APPEAL = f"{INSURANCE}/claim-status-appeal"
INSURANCE_CLAIM_STATUS_PRINT = f"{INSURANCE}/claim-status-print"

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
RECORDS_RESTORE_DEATH = f"{RECORDS}/death-restore"
RECORDS_DEATH_CERTIFICATE = f"{RECORDS}/death-certificate"

RECORDS_BIRTH = f"/{RECORDS}/birth"
RECORDS_BIRTH_CERTIFICATE = f"{RECORDS}/birth-certificate"
RECORDS_ADD_BIRTH = f"{RECORDS}/add-birth"
RECORDS_BIRTH_DELETE = f"{RECORDS}/birth-delete"
RECORDS_BIRTH_EDIT = f"{RECORDS}/birth-edit"
RESTORE_RECORDS_BIRTH = f"{RECORDS}/restore-birth"

RECORDS_BIRTH_MEDICAL_VISIT = f"{RECORDS}/birth-visit"
RECORDS_BIRTH_ADD_MEDICAL_VISIT = f"{RECORDS}/add-birth-visit"
RECORDS_BIRTH_EDIT_MEDICAL_VISIT = f"{RECORDS}/birth-edit-visit"
RECORDS_BIRTH_MEDICAL_VISIT_DELETE = f"{RECORDS}/birth-visit-delete"
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
STAFF_ADD = f"{STAFF}/add-staff"
STAFF_EDIT = f"{STAFF}/edit-staff"
STAFF_DELETE = f"{STAFF}/delete-staff"
STAFF_RESTORE = f"{STAFF}/restore-staff"


# treatments
TREATMENTS = "/treatments"
TREATMENTS_ADD = f"{TREATMENTS}/add-treatments"
TREATMENTS_EDIT = f"{TREATMENTS}/edit-treatments"
TREATMENTS_TOGGLE_STATUS = f"{TREATMENTS}/toggle-status"
TREATMENTS_DELETE = f"{TREATMENTS}/delete-treatments"
TREATMENTS_RESTORE = f"{TREATMENTS}/restore-treatments"
