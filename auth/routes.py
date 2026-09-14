from fastapi import APIRouter, Depends, HTTPException, status
from auth.schemas import LoginRequest, TokenResponse, AuthenticatedUser, RegisterRequest
from auth.service import authenticate_user, register_user
from auth.security import create_access_token
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.identifier, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=access_token)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    if len(request.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
        
    result = register_user(request.username, request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=result["status"], detail=result["error"])
        
    return {"message": "User registered successfully"}

@router.get("/me", response_model=AuthenticatedUser)
def read_users_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    return current_user
