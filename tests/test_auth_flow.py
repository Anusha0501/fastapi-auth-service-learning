from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_auth_flow_register_login_me_refresh():
    email = "learner@example.com"
    password = "correct horse battery staple"

    register_response = client.post("/auth/register", json={"email": email, "password": password})
    assert register_response.status_code in {201, 409}

    login_response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email

    refresh_response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"] != tokens["access_token"]
