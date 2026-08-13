from app.core.security import create_access_token, create_refresh_token
from app.models.user import User


def test_refresh_rejects_access_token(client, db_session):
    user = User(email="refresh@test.com", password_hash="fake")
    db_session.add(user)
    db_session.commit()

    access_token = create_access_token(user_id=user.id)
    refresh_token = create_refresh_token(user_id=user.id)

    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401

    valid_response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert valid_response.status_code == 200
    assert "access_token" in valid_response.json()
