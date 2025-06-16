from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_app.db.session import get_async_session
from fastapi_app.models.exam_rules import ExamsRules
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_app.schemas.exam_rules import ExamsRulesCreate

router = APIRouter()

@router.get("/exam-rules/")
async def get_exam_rules():
    return {"rule": "no cheating"}

# @router.post("/exam-rules/", status_code=status.HTTP_201_CREATED)
# async def create_exam_rule(
#     data: ExamsRulesCreate,
#     session: AsyncSession = Depends(get_async_session)
# ):
#     new_rule = ExamsRules(rules=data.rules)
#     session.add(new_rule)
#     await session.commit()
#     await session.refresh(new_rule)
#     return {
#         "id": new_rule.id,
#         "rules": new_rule.rules,
#         "created": new_rule.created,
#         "updated": new_rule.updated,
#     }


# @router.get("/exam-rules/")
# async def list_exam_rules(session: AsyncSession = Depends(get_async_session)):
#     result = await session.execute(select(ExamsRules))
#     exam_rules = result.scalars().all()
#     return [
#         {
#             "id": rule.id,
#             "rules": rule.rules,
#             "created": rule.created,
#             "updated": rule.updated,
#         }
#         for rule in exam_rules
#     ]
