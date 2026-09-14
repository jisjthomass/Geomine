from auth.database import get_db_connection
from auth.security import verify_password, get_password_hash
from auth.schemas import AuthenticatedUser
from psycopg2.extras import DictCursor
import psycopg2

def authenticate_user(identifier: str, password: str) -> AuthenticatedUser | None:
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                "SELECT id, username, email, password_hash, is_active FROM users WHERE username = %s OR email = %s",
                (identifier, identifier)
            )
            user_row = cursor.fetchone()
            
            if not user_row:
                return None
                
            if not verify_password(password, user_row['password_hash']):
                return None
                
            if not user_row['is_active']:
                return None
                
            return AuthenticatedUser(
                id=user_row['id'],
                username=user_row['username'],
                email=user_row['email'],
                is_active=user_row['is_active']
            )
    except Exception as e:
        print(f"Database error during authentication: {e}")
        return None
    finally:
        conn.close()

def get_user(username: str) -> AuthenticatedUser | None:
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                "SELECT id, username, email, is_active FROM users WHERE username = %s",
                (username,)
            )
            user_row = cursor.fetchone()
            
            if not user_row:
                return None
                
            return AuthenticatedUser(
                id=user_row['id'],
                username=user_row['username'],
                email=user_row['email'],
                is_active=user_row['is_active']
            )
    except Exception as e:
        print(f"Database error fetching user: {e}")
        return None
    finally:
        conn.close()

def register_user(username: str, email: str, password: str) -> dict:
    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Database connection failed", "status": 500}
        
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return {"success": False, "error": "Username already exists", "status": 409}
                
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return {"success": False, "error": "Email already exists", "status": 409}
                
            hashed_password = get_password_hash(password)
            
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, role, is_active) 
                VALUES (%s, %s, %s, 'engineer', TRUE)
                """,
                (username, email, hashed_password)
            )
            conn.commit()
            return {"success": True, "error": None, "status": 201}
    except psycopg2.Error as e:
        conn.rollback()
        return {"success": False, "error": f"Database error: {str(e)}", "status": 500}
    finally:
        conn.close()
