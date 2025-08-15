def get_user_by_email(email):
    """Check if a user exists in DB by email"""
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[DB ERROR] get_user_by_email: {e}")
        return None

def add_user(email, password):
    """Add new user to DB with is_verified=False"""
    try:
        response = supabase.table("users").insert({
            "email": email,
            "password": password,  # Ideally hash this before storing
            "is_verified": False
        }).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[DB ERROR] add_user: {e}")
        return None

def mark_verified(email):
    """Set user.is_verified=True"""
    try:
        supabase.table("users").update({"is_verified": True}).eq("email", email).execute()
        return True
    except Exception as e:
        print(f"[DB ERROR] mark_verified: {e}")
        return False

def delete_user(email):
    """Delete a user from DB"""
    try:
        response = supabase.table("users").delete().eq("email", email).execute()
        if response.data and len(response.data) > 0:
            return {"success": True, "message": f"User {email} deleted"}
        else:
            return {"success": False, "message": f"User {email} not found or deletion blocked"}
    except Exception as e:
        print(f"[DB ERROR] delete_user: {e}")
        return {"success": False, "message": str(e)}

def generate_jwt(email):
    """Generate a JWT token for login sessions"""
    import jwt, datetime
    payload = {
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_jwt(token):
    """Decode JWT and return email if valid"""
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["email"]
    except ExpiredSignatureError:
        return None
    except InvalidTokenError:
        return None
