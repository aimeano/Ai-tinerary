from app.auth.jwt_utils import create_access_token, decode_access_token

user_id = "user_test_123"

token = create_access_token(user_id)

print("TOKEN:")
print(token)

decoded = decode_access_token(token)

print("\nDECODED:")
print(decoded)

assert decoded["sub"] == user_id

print("\nJWT test passed.")