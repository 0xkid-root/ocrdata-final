from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class VoterData(BaseModel):
    name: str
    gender: str
    age: str
    voter_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class ProcessingResponse(BaseModel):
    status: str
    data: List[Dict[str, str]]
    message: str
    warnings: Optional[List[str]] = None