"""
POST /corrections — Ticket 10.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.services import corrections_service

router = APIRouter()


class CorrectionRequest(BaseModel):
    report_id: str
    field_corrected: str
    corrected_value: str


class CorrectionResponse(BaseModel):
    status: str


@router.post("/corrections", response_model=CorrectionResponse)
def submit_correction(request: CorrectionRequest):
    try:
        corrections_service.submit_correction(
            request.report_id, request.field_corrected, request.corrected_value
        )
    except corrections_service.ReportNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="This report may have been removed or reprocessed — please refresh and try again.",
        )
    except corrections_service.InvalidFieldError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CorrectionResponse(status="saved")
