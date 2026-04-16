import re

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_phone(phone):
    return re.match(r"^[0-9]{10}$", phone)

def validate_experience(exp):
    try:
        return float(exp) >= 0
    except:
        return False