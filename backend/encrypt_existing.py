from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_model import Base, Messages
from utils import encrypt_message, load_key

# Load encryption key
key = load_key()

# Connect to DB
engine = create_engine("sqlite:///./backend/Arkham_DB.db")
Session = sessionmaker(bind=engine)
session = Session()

# Encrypt all plaintext messages
messages = session.query(Messages).all()
for msg in messages:
    if not msg.content.startswith("gAAAA"):  # Basic check to skip already encrypted messages
        print(f"Encrypting message {msg.messageId}")
        encrypted_content = encrypt_message(msg.content, key)
        msg.content = encrypted_content

session.commit()
session.close()
print("✅ All messages encrypted.")
