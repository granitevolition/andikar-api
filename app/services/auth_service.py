from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.models.auth import UserInDB, UserCreate
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.users_db = {}  # Replace with actual database
        
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    async def create_user(self, user: UserCreate) -> UserInDB:
        # Check if user exists
        if any(u.email == user.email for u in self.users_db.values()):
            raise ValueError("Email already registered")
            
        user_id = str(uuid.uuid4())
        api_key = f"sk-{str(uuid.uuid4())}"
        
        db_user = UserInDB(
            id=user_id,
            email=user.email,
            username=user.username,
            hashed_password=self.get_password_hash(user.password),
            api_key=api_key
        )
        
        self.users_db[user_id] = db_user
        return db_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        user = next((u for u in self.users_db.values() if u.email == email), None)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        return user
    
    async def get_user_by_api_key(self, api_key: str) -> Optional[UserInDB]:
        return next((u for u in self.users_db.values() if u.api_key == api_key), None)