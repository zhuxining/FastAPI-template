import secrets
import string


def random_lower_string(length: int = 12) -> str:
    alphabet = string.ascii_lowercase
    return "".join(secrets.choice(alphabet) for _ in range(length))


def random_email() -> str:
    local_part = random_lower_string(8)
    domain = random_lower_string(5)
    return f"{local_part}@{domain}.com"
