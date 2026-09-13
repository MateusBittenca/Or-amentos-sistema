import uuid
from fastapi.testclient import TestClient
import pytest

from main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        test_client.headers.update({"Accept": "application/json"})
        yield test_client


def unique_email(prefix="t"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}@test.local"


def register_and_login(client, email=None, password="senha1234"):
    email = email or unique_email()
    created = client.post("/register", json={"nome": email, "password": password, "nome_exibicao": "Teste User"})
    assert created.status_code == 200, created.text
    token_response = client.post("/token", data={"username": email, "password": password})
    assert token_response.status_code == 200, token_response.text
    payload = token_response.json()
    return {
        "email": email,
        "password": password,
        "token": payload["access_token"],
        "user": payload["user"],
        "headers": {"Authorization": f"Bearer {payload['access_token']}", "Accept": "application/json"},
    }


def create_obra(client, headers, nome=None):
    nome = nome or f"Obra {uuid.uuid4().hex[:6]}"
    response = client.post("/obras", json={"nome": nome, "descricao": "teste"}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def add_activity(client, headers, obra_id, nome="Atividade teste", valor="100", setor="Projeto", data="2026-09-13"):
    response = client.post(
        f"/add-activity?obra_id={obra_id}",
        data={"atividade": nome, "valor": valor, "setor": setor, "data": data},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def invite_and_accept(client, owner_headers, obra_id, papel, guest=None):
    guest = guest or register_and_login(client)
    invite = client.post(
        f"/obras/{obra_id}/convites",
        json={"papel": papel},
        headers=owner_headers,
    )
    assert invite.status_code == 200, invite.text
    token = invite.json()["token"]
    accepted = client.post(f"/convite/{token}/aceitar", headers=guest["headers"])
    assert accepted.status_code == 200, accepted.text
    guest["obra_id"] = obra_id
    guest["papel"] = papel
    return guest
