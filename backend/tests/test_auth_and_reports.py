import io

from app.core.security import create_access_token
from app.domain.enums import Role


def _token(role: Role, user_id: str = "u1") -> str:
    return create_access_token(user_id, f"{role.value}@test.com", role, f"Test {role.value}")


def _auth_header(role: Role, user_id: str = "u1") -> dict:
    return {"Authorization": f"Bearer {_token(role, user_id)}"}


def test_reports_requires_auth(client):
    response = client.get("/api/reports")
    assert response.status_code in (401, 403)


def test_create_and_list_report_as_citizen(client):
    files = {"file": ("test.jpg", io.BytesIO(b"\xff\xd8\xff\xe0fakejpegbytes\xff\xd9"), "image/jpeg")}
    create_resp = client.post(
        "/api/reports?lat=28.7&lng=77.1",
        headers=_auth_header(Role.CITIZEN, "citizen-1"),
        files=files,
    )
    assert create_resp.status_code == 201
    report = create_resp.json()
    assert report["status"] == "Pending"
    assert report["reported_by"] == "citizen-1"

    list_resp = client.get("/api/reports", headers=_auth_header(Role.CITIZEN, "citizen-1"))
    assert list_resp.status_code == 200
    assert any(r["id"] == report["id"] for r in list_resp.json())


def test_citizen_cannot_update_status(client):
    response = client.patch(
        "/api/reports/nonexistent/status",
        headers=_auth_header(Role.CITIZEN),
        json={"status": "Resolved"},
    )
    assert response.status_code == 403


def test_authority_can_update_status_of_missing_report(client):
    response = client.patch(
        "/api/reports/nonexistent/status",
        headers=_auth_header(Role.AUTHORITY),
        json={"status": "Resolved"},
    )
    assert response.status_code == 404
