from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.copilot import CopilotChatRequest, CopilotChatResponse
from app.services.copilot_service import chat_with_copilot


router = APIRouter()


@router.post("/chat", response_model=CopilotChatResponse)
async def chat(
    payload: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
) -> CopilotChatResponse:
    _ = current_user
    return await chat_with_copilot(payload)
