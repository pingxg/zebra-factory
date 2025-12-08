from werkzeug.security import generate_password_hash


hashed_password = generate_password_hash("123456", method='pbkdf2:sha256')
print(hashed_password)
