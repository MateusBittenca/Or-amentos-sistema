from tests.conftest import add_activity, create_obra, invite_and_accept, register_and_login


def test_nao_membro_nao_acessa_obra(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    outsider = register_and_login(client)
    response = client.get(f"/atividades?obra_id={obra['id']}", headers=outsider["headers"])
    assert response.status_code == 403


def test_leitura_nao_adiciona_atividade(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    reader = invite_and_accept(client, owner["headers"], obra["id"], "leitura")
    response = client.post(
        f"/add-activity?obra_id={obra['id']}",
        data={"atividade": "X", "valor": "10", "setor": "Projeto", "data": "2026-09-13"},
        headers=reader["headers"],
    )
    assert response.status_code == 403


def test_leitura_nao_paga(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    activity = add_activity(client, owner["headers"], obra["id"])
    reader = invite_and_accept(client, owner["headers"], obra["id"], "leitura")
    response = client.post(
        f"/register-payment?obra_id={obra['id']}",
        data={
            "atividade_id": activity["id"],
            "usuario_id": reader["user"]["id"],
            "value": "10",
        },
        headers=reader["headers"],
    )
    assert response.status_code == 403


def test_membro_nao_adiciona_atividade(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    member = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    response = client.post(
        f"/add-activity?obra_id={obra['id']}",
        data={"atividade": "X", "valor": "10", "setor": "Projeto", "data": "2026-09-13"},
        headers=member["headers"],
    )
    assert response.status_code == 403


def test_membro_nao_paga_em_nome_de_outro(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    activity = add_activity(client, owner["headers"], obra["id"])
    member = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    response = client.post(
        f"/register-payment?obra_id={obra['id']}",
        data={
            "atividade_id": activity["id"],
            "usuario_id": owner["user"]["id"],
            "value": "10",
        },
        headers=member["headers"],
    )
    assert response.status_code == 403


def test_membro_paga_o_proprio(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    activity = add_activity(client, owner["headers"], obra["id"])
    member = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    response = client.post(
        f"/register-payment?obra_id={obra['id']}",
        data={
            "atividade_id": activity["id"],
            "usuario_id": member["user"]["id"],
            "value": "10",
        },
        headers=member["headers"],
    )
    assert response.status_code == 200, response.text


def test_pagamento_nao_excede_restante(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    activity = add_activity(client, owner["headers"], obra["id"], valor="20")
    response = client.post(
        f"/register-payment?obra_id={obra['id']}",
        data={
            "atividade_id": activity["id"],
            "usuario_id": owner["user"]["id"],
            "value": "50",
        },
        headers=owner["headers"],
    )
    assert response.status_code == 400


def test_pagamento_usa_atividade_id(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    first = add_activity(client, owner["headers"], obra["id"], nome="Mesmo nome", valor="40")
    second = add_activity(client, owner["headers"], obra["id"], nome="Mesmo nome", valor="80")
    paid = client.post(
        f"/register-payment?obra_id={obra['id']}",
        data={
            "atividade_id": second["id"],
            "usuario_id": owner["user"]["id"],
            "value": "80",
        },
        headers=owner["headers"],
    )
    assert paid.status_code == 200, paid.text
    listing = client.get(f"/atividades?obra_id={obra['id']}", headers=owner["headers"])
    by_id = {item["id"]: item for item in listing.json()}
    assert by_id[first["id"]]["total_pago"] == 0
    assert by_id[second["id"]]["total_pago"] == 80
