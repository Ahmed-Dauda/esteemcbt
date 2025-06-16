from pydantic import BaseModel
from typing import Optional

class ExamsRulesCreate(BaseModel):
    rules: Optional[str] = None
