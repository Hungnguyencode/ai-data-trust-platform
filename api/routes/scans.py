from fastapi import APIRouter

router = APIRouter()


@router.get("/history")
def get_scan_history():
    """
    Minimal endpoint.
    SQL Server scan history is still handled by the Streamlit Reports page.
    This route exists to make the API layer ready for future backend integration.
    """
    return {
        "message": "Scan history API placeholder is active.",
        "note": "Full SQL Server integration can be connected in Version 2.2 or 3.0.",
        "items": [],
    }


@router.get("/latest")
def get_latest_scan():
    return {
        "message": "Latest scan API placeholder is active.",
        "latest_scan": None,
    }