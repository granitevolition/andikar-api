from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from app.core.config import settings
from app.services.auth_service import AuthService
from app.models.auth import UserInDB

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends()
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = auth_service.users_db.get(user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_from_api_key(
    api_key: str = Depends(api_key_header),
    auth_service: AuthService = Depends()
) -> UserInDB:
    user = await auth_service.get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return user