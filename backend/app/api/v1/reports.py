import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.agents.complaint_agent import ComplaintAgent
from app.api.deps import get_complaint_agent_dep, get_report_repository_dep, get_storage_service_dep
from app.core.security import get_current_user, require_roles
from app.domain.enums import Role
from app.domain.schemas import AuthenticatedUser, Report, ReportStatusUpdate
from app.repositories.base_repository import ReportRepositoryProtocol
from app.services.storage_service import StorageService

router = APIRouter(prefix="/reports", tags=["reports"])

_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("", response_model=Report, status_code=status.HTTP_201_CREATED)
async def create_report(
    lat: float,
    lng: float,
    file: UploadFile = File(...),
    complaint_agent: ComplaintAgent = Depends(get_complaint_agent_dep),
    storage_service: StorageService = Depends(get_storage_service_dep),
    report_repository: ReportRepositoryProtocol = Depends(get_report_repository_dep),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Citizen reporting endpoint.
    Sends the uploaded image to the Complaint Agent (Gemini Vision) to
    classify issue type, estimate severity, and assign a priority score;
    stores the photo in Cloud Storage and the report in Firestore.
    """
    image_bytes = await file.read()
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image exceeds 10MB limit.")
    if not image_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty.")

    classification = await complaint_agent.classify_image(image_bytes, file.content_type or "image/jpeg")
    image_url = await storage_service.upload_report_image(image_bytes, file.content_type or "image/jpeg")

    report = Report(
        id=str(uuid.uuid4()),
        category=classification.category,
        severity=classification.severity,
        priority=classification.priority,
        department=classification.department,
        justification=classification.justification,
        lat=lat,
        lng=lng,
        image_url=image_url,
        reported_by=user.id,
    )
    return await report_repository.create(report)


@router.get("", response_model=list[Report])
async def list_reports(
    sort_by_priority: bool = True,
    report_repository: ReportRepositoryProtocol = Depends(get_report_repository_dep),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Authorities/Admins see every report; Citizens see their own submissions."""
    if user.role in (Role.AUTHORITY, Role.ADMIN):
        return await report_repository.list_all(sort_by_priority=sort_by_priority)
    return await report_repository.list_for_user(user.id)


@router.patch("/{report_id}/status", response_model=Report)
async def update_status(
    report_id: str,
    payload: ReportStatusUpdate,
    report_repository: ReportRepositoryProtocol = Depends(get_report_repository_dep),
    _: AuthenticatedUser = Depends(require_roles([Role.AUTHORITY, Role.ADMIN])),
):
    updated = await report_repository.update_status(report_id, payload.status.value)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    return updated
