from app.core.security import create_access_token
from app.models.user import User


def test_user_b_cannot_access_subscription_of_user_a(client, db_session):
    user_a = User(email="a@test.com", password_hash="fake")
    user_b = User(email="b@test.com", password_hash="fake")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(user_id=user_a.id)
    token_b = create_access_token(user_id=user_b.id)

    create_response = client.post(
        "/subscriptions",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "name": "Netflix",
            "amount": "199.00",
            "currency": "MXN",
            "billing_cycle": "monthly",
            "start_date": "2026-01-31",
        },
    )
    assert create_response.status_code == 201
    subscription_id = create_response.json()["id"]

    response = client.get(
        f"/subscriptions/{subscription_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 404

    list_response = client.get(
        "/subscriptions", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert list_response.status_code == 200
    assert list_response.json() == []
