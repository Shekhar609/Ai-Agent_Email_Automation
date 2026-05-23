from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflow import run_workflow
from app.api.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.db.models import Email, User
from app.schemas.workflow import RunRequest, RunResponse

router = APIRouter()


@router.post("/run", response_model=RunResponse)
@limiter.limit("20/minute")
async def run(
    request: Request,
    body: RunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    email = await db.get(Email, body.email_id)
    if email is None or email.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "email not found")

    result = await run_workflow(str(body.email_id), str(user.id))
    return RunResponse(**result)
