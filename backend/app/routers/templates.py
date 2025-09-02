from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.esrs.registry import load_registry

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("/datapoints.csv", response_class=PlainTextResponse)
async def template_datapoints_csv():
    codes = ",".join(sorted(load_registry().keys()))
    lines = [
        "# erlaubte Codes: " + codes,
        "esrs_code,value,unit,source",
        "E1.S1.TOTAL,0,tCO2e,manual"
    ]
    return "\n".join(lines)
