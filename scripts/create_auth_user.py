import os
import argparse
import getpass
import psycopg2
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

def main():
    parser = argparse.ArgumentParser(description="Create a prototype authentication user.")
    parser.add_argument("--username", required=True, help="The username for the new user")
    parser.add_argument("--role", default="engineer", help="The role of the new user")
    parser.add_argument("--email", default=None, help="The email of the new user")
    
    args = parser.parse_args()
    
    password = getpass.getpass(f"Enter password for {args.username}: ")
    if not password:
        print("Password cannot be empty.")
        return
        
    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("Passwords do not match.")
        return
        
    # Hash password
    password_hash_engine = PasswordHash((Argon2Hasher(),))
    hashed_password = password_hash_engine.hash(password)
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            dbname=os.getenv("DB_NAME", "nwis_wells_db"),
            port=os.getenv("DB_PORT", "5432")
        )
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON CONFLICT (username) DO UPDATE 
            SET password_hash = EXCLUDED.password_hash,
                email = EXCLUDED.email,
                role = EXCLUDED.role,
                is_active = TRUE;
            """,
            (args.username, args.email, hashed_password, args.role)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"User '{args.username}' created/updated successfully.")
    except Exception as e:
        print(f"Error creating user: {e}")

if __name__ == "__main__":
    main()
