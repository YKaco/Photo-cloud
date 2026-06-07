from app import get_user
from werkzeug.security import check_password_hash

user = get_user("k")

print(check_password_hash(user[1], "k"))
