from werkzeug.security import generate_password_hash, check_password_hash

hashed_password = generate_password_hash("Spartao2023!")
print(hashed_password)

print(check_password_hash(hashed_password, 'Spartao2023!'))




# generate_password_hash("plain_text_password")