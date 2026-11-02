from backend.core.security import get_password_hash

MOCK_USERS_DB = {
    "doc_john": {"username": "doc_john", "password": get_password_hash("password123"), "role": "doctor"},
    "nurse_joy": {"username": "nurse_joy", "password": get_password_hash("password123"), "role": "nurse"},
    "bill_smith": {"username": "bill_smith", "password": get_password_hash("password123"), "role": "billing_executive"},
    "tech_tom": {"username": "tech_tom", "password": get_password_hash("password123"), "role": "technician"},
}

def get_user(username: str):
    return MOCK_USERS_DB.get(username)
