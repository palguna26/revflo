from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.ai_review import ai_service
from app.models.user import User
from app.api.v1.endpoints.me import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

class FixRequest(BaseModel):
    issue_description: str
    code_snippet: str

class FixResponse(BaseModel):
    fixed_code: str

@router.post("/fix", response_model=FixResponse)
async def generate_fix(req: FixRequest, current_user: User = Depends(get_current_user)):
    """
    Generate a code fix using QodoEngine.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    try:
        fixed = await ai_service.qodo.generate_fix(req.issue_description, req.code_snippet)
        return {"fixed_code": fixed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
