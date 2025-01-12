from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import AuthService
from app.models.auth import UserCreate, Token, UserResponse

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    try:
        db_user = await auth_service.create_user(user)
        return db_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)

@router.post("/refresh-api-key", response_model=UserResponse)
async def refresh_api_key(
    current_user: UserInDB = Depends(get_current_user_from_token)
):
    current_user.api_key = f"sk-{str(uuid.uuid4())}"
    return current_user