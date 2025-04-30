#region Imports
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="../frontend/templates")


from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db_model import Base, Users, Messages
from api_model import UsersModel, MessagesModel, BaseModel

from utils import load_key, encrypt_message, decrypt_message

import bcrypt
import api_model
#endregion

#region FastAPI APP Setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:5000"] if you want to be specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#endregion

#region DB Connection
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "Arkham_DB.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
#endregion

#region Bcrypt Setup
passSalt = bcrypt.gensalt()
def passencrypt (username: str, password: str):
    s = 1
def passcompare (username: str, password: str):
    isUser = get_users(username=username)

    if isUser == username:
        isUser
        bcrypt.checkpw

#endregion

#region Login Endpoints
# Pydantic model for login request
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login_user(login: LoginRequest, db: Session = Depends(get_db)):
    username = login.username
    password = login.password

    print("🔐 Incoming login:", username)

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    print("📦 Stored password hash:", user.password)
    print("🧪 Checking password match...")

    try:
        match = bcrypt.checkpw(password.encode(), user.password.encode())
        print("✅ Password match result:", match)
    except Exception as e:
        print("⚠️ Error during password check:", e)
        raise HTTPException(status_code=500, detail="Server error")

    if match:
        return {
            "success": True,
            "message": "Login successful",
            "user_id": user.userId,
            "username": user.username
        }

    print("❌ Password mismatch.")
    raise HTTPException(status_code=401, detail="Invalid username or password")
#endregion
#region User Endpoints

#Get All Users
@app.get("/users/")
async def get_users(db: Session = Depends(get_db)):
    results = db.query(Users).all()
    users_list = []
    for user in results:
        users_list.append({
            "userId": user.userId,
            "username": user.username,
            "password": user.password,
            "profilePic": user.profilePic
        })
    return users_list

#Get User by Username
@app.get("/users/username/{username}")
async def get_user_by_username(username: str, db: Session = Depends(get_db)):
    result = db.query(Users).filter(Users.username == username).first()
    return result

#Get User by userId
@app.get("/users/{userId}")
async def get_users_by_id(userId:int, db:Session=Depends(get_db)):
    results = db.query(Users).filter(Users.userId == userId).first()
    return results

#Create New User
@app.post("/users/")
async def create_user(user: UsersModel, db: Session = Depends(get_db)):
    orm_user = Users(**user.model_dump())
    if not orm_user.profilePic:
        orm_user.profilePic = "default.png"  # fallback if not provided
    db.add(orm_user)
    db.commit()

#Edit User

#Delete User

#endregion

#region Message Endpoints

#Get Message by Title/All

@app.get("/messages/")
async def get_messages(title: str | None=None, db:Session=Depends(get_db)):
    if not title:
        results = db.query(Messages).all()
        return results
    else:
        results = db.query(Messages).filter(Messages.title == title).first()
        return results
    
#Get message by reciever (THis is good for showing only messages meant for the currently active account)
@app.get("/messages/received/{user_id}")
async def get_received_messages(user_id: int, db: Session = Depends(get_db)):
    messages = db.query(Messages).filter(Messages.userIdReceiver == user_id).all()
    return messages

#Get message by sender (To get the list of messages you sent)
@app.get("/messages/sent/{user_id}")
async def get_sent_messages(user_id: int, db: Session= Depends(get_db)):
    messages = db.query(Messages).filter(Messages.userIdSender == user_id).all()
    return messages


@app.get("/messages/conversation/{current_user_id}/{other_user_id}")
async def get_conversation(current_user_id: int, other_user_id: int, db: Session = Depends(get_db)):
    key = load_key()
    messages = db.query(Messages).filter(
        ((Messages.userIdSender == current_user_id) & (Messages.userIdReceiver == other_user_id)) |
        ((Messages.userIdSender == other_user_id) & (Messages.userIdReceiver == current_user_id))
    ).order_by(Messages.messageDate.asc()).all()

    # Decrypt message contents
    for msg in messages:
        try:
            msg.content = decrypt_message(msg.content, key)
        except Exception:
            msg.content = "[ERROR: Decryption failed]"

    return messages


#Get Message by messageId
@app.get("/messages/{messageId}")
async def get_messages_by_id(messageId: int | None=None, db:Session=Depends(get_db)):
    results = db.query(Messages).filter(Messages.messageId == messageId).first()
    return results

#Create New Message
@app.post("/messages/")
async def create_message(message: MessagesModel, db: Session = Depends(get_db)):
    key = load_key()
    encrypted_content = encrypt_message(message.content, key)
    orm_message = Messages(
        content=encrypted_content,
        userIdSender=message.userIdSender,
        userIdReceiver=message.userIdReceiver,
        isRead=message.isRead,
        messageDate=message.messageDate
    )
    db.add(orm_message)
    db.commit()
#Edit Message

#Delete Message

#
@app.get("/conversation/{other_user_id}", response_class=HTMLResponse)
async def conversation_page(request: Request, other_user_id: int):
    return templates.TemplateResponse("conversation.html", {
        "request": request,
        "other_user_id": other_user_id
    })



#endregion