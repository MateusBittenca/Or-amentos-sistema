from datetime import datetime, timedelta

from database import db_cursor
from tests.conftest import create_obra, register_and_login


def test_convite_expirado(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    invite = client.post(
        f"/obras/{obra['id']}/convites",
        json={"papel": "membro"},
        headers=owner["headers"],
    )
    assert invite.status_code == 200, invite.text
    token = invite.json()["token"]
    with db_cursor() as cursor:
        cursor.execute(
            "UPDATE convites SET expira_em = %s WHERE token = %s",
            (datetime.utcnow() - timedelta(days=1), token),
        )
    response = client.get(f"/convite/{token}")
    assert response.status_code == 400
    guest = register_and_login(client)
    accept = client.post(f"/convite/{token}/aceitar", headers=guest["headers"])
    assert accept.status_code == 400


def test_convite_ja_utilizado(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    invite = client.post(
        f"/obras/{obra['id']}/convites",
        json={"papel": "membro"},
        headers=owner["headers"],
    )
    token = invite.json()["token"]
    guest = register_and_login(client)
    first = client.post(f"/convite/{token}/aceitar", headers=guest["headers"])
    assert first.status_code == 200, first.text
    other = register_and_login(client)
    second = client.post(f"/convite/{token}/aceitar", headers=other["headers"])
    assert second.status_code == 400
