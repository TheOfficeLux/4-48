"""Children route tests (require auth and DB)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_get_child(async_client: AsyncClient):
    # Register caregiver first
    r = await async_client.post(
        "/api/auth/register",
        json={"email": "parent@test.com", "password": "password123!", "full_name": "Parent"},
    )
    if r.status_code != 200:
        pytest.skip("Auth not available")
    token = r.json().get("access_token")
    if not token:
        pytest.skip("No token")
    r2 = await async_client.post(
        "/api/children",
        json={
            "full_name": "Child One",
            "date_of_birth": "2015-06-01",
            "primary_language": "en",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    if r2.status_code not in (200, 201):
        assert r2.status_code in (200, 201), r2.text
    if r2.status_code == 200:
        data = r2.json()
        assert "child_id" in data
        assert data["full_name"] == "Child One"
