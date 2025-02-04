from werkzeug.security import generate_password_hash, check_password_hash

# Generate hash for 'admin' password
password = 'admin'
hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

# Verify the hash works
assert check_password_hash(hash, password)

print(f"Hash for password '{password}': {hash}")
