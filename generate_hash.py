from werkzeug.security import generate_password_hash

password = 'admin'
hash = generate_password_hash(password)
print(f"Password hash for '{password}': {hash}")
