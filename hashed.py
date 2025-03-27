from werkzeug.security import generate_password_hash, check_password_hash

# Step 1: Choose a strong password
original_password = "AdminSecure2024!"

# Step 2: Generate the hash
hashed_password = generate_password_hash(original_password, method='pbkdf2:sha256')

# Step 3: Print the hashed password
print("Original Password:", original_password)
print("Hashed Password:", hashed_password)

# Step 4: Verify the hash
is_correct = check_password_hash(hashed_password, original_password)
print("Password Verification:", is_correct)