import json

from tests.conftest import add_activity, create_obra, invite_and_accept, register_and_login


def _resumo(client, headers, obra_id):
    response = client.get(f"/obras/{obra_id}/resumo", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def _pagar(client, headers, obra_id, atividade_id, usuario_id, value):
    response = client.post(
        f"/register-payment?obra_id={obra_id}",
        data={"atividade_id": atividade_id, "usuario_id": usuario_id, "value": value},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response


def test_resumo_agregado_e_saldos(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    activity = add_activity(client, owner["headers"], obra["id"], valor="100")
    _pagar(client, owner["headers"], obra["id"], activity["id"], owner["user"]["id"], "100")

    data = _resumo(client, owner["headers"], obra["id"])
    assert data["total"] == 100
    assert data["total_pago"] == 100
    assert data["restante"] == 0
    assert len(data["saldos"]) == 2
    by_id = {item["usuario_id"]: item for item in data["saldos"]}
    owner_saldo = by_id[owner["user"]["id"]]
    partner_saldo = by_id[partner["user"]["id"]]
    assert owner_saldo["parte"] == 50
    assert owner_saldo["pago"] == 100
    assert owner_saldo["saldo"] == -50
    assert partner_saldo["parte"] == 50
    assert partner_saldo["pago"] == 0
    assert partner_saldo["saldo"] == 50
    assert len(data["transferencias"]) == 1
    transferencia = data["transferencias"][0]
    assert transferencia["de_usuario_id"] == partner["user"]["id"]
    assert transferencia["para_usuario_id"] == owner["user"]["id"]
    assert transferencia["valor"] == 50


def test_resumo_nao_membro(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    outsider = register_and_login(client)
    response = client.get(f"/obras/{obra['id']}/resumo", headers=outsider["headers"])
    assert response.status_code == 403


def test_pagamento_parcial_rateia_so_o_pago(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    activity = add_activity(client, owner["headers"], obra["id"], valor="100")
    _pagar(client, owner["headers"], obra["id"], activity["id"], owner["user"]["id"], "40")

    data = _resumo(client, owner["headers"], obra["id"])
    assert data["total"] == 100
    assert data["total_pago"] == 40
    assert data["restante"] == 60
    by_id = {item["usuario_id"]: item for item in data["saldos"]}
    assert by_id[owner["user"]["id"]]["parte"] == 20
    assert by_id[owner["user"]["id"]]["pago"] == 40
    assert by_id[owner["user"]["id"]]["saldo"] == -20
    assert by_id[partner["user"]["id"]]["parte"] == 20
    assert by_id[partner["user"]["id"]]["pago"] == 0
    assert by_id[partner["user"]["id"]]["saldo"] == 20
    assert data["transferencias"][0]["valor"] == 20
    assert data["transferencias"][0]["de_usuario_id"] == partner["user"]["id"]
    assert data["transferencias"][0]["para_usuario_id"] == owner["user"]["id"]


def test_leitura_fora_do_rateio(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    reader = invite_and_accept(client, owner["headers"], obra["id"], "leitura")
    activity = add_activity(client, owner["headers"], obra["id"], valor="100")
    _pagar(client, owner["headers"], obra["id"], activity["id"], owner["user"]["id"], "100")

    data = _resumo(client, owner["headers"], obra["id"])
    ids = {item["usuario_id"] for item in data["saldos"]}
    assert reader["user"]["id"] not in ids
    assert ids == {owner["user"]["id"], partner["user"]["id"]}
    by_id = {item["usuario_id"]: item for item in data["saldos"]}
    assert by_id[owner["user"]["id"]]["parte"] == 50
    assert by_id[partner["user"]["id"]]["parte"] == 50


def test_participacao_70_30(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    updated = client.patch(
        f"/obras/{obra['id']}/participacao",
        json={
            "participantes": [
                {"usuario_id": owner["user"]["id"], "percentual": 70},
                {"usuario_id": partner["user"]["id"], "percentual": 30},
            ]
        },
        headers=owner["headers"],
    )
    assert updated.status_code == 200, updated.text
    activity = add_activity(client, owner["headers"], obra["id"], valor="100")
    _pagar(client, owner["headers"], obra["id"], activity["id"], owner["user"]["id"], "100")

    data = _resumo(client, owner["headers"], obra["id"])
    by_id = {item["usuario_id"]: item for item in data["saldos"]}
    assert by_id[owner["user"]["id"]]["parte"] == 70
    assert by_id[owner["user"]["id"]]["pago"] == 100
    assert by_id[owner["user"]["id"]]["saldo"] == -30
    assert by_id[partner["user"]["id"]]["parte"] == 30
    assert by_id[partner["user"]["id"]]["pago"] == 0
    assert by_id[partner["user"]["id"]]["saldo"] == 30
    assert data["transferencias"][0]["de_usuario_id"] == partner["user"]["id"]
    assert data["transferencias"][0]["para_usuario_id"] == owner["user"]["id"]
    assert data["transferencias"][0]["valor"] == 30


def test_membro_que_entra_depois_nao_herda_atividade(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    activity = add_activity(client, owner["headers"], obra["id"], valor="100")
    _pagar(client, owner["headers"], obra["id"], activity["id"], owner["user"]["id"], "100")
    novo = invite_and_accept(client, owner["headers"], obra["id"], "membro")

    data = _resumo(client, owner["headers"], obra["id"])
    by_id = {item["usuario_id"]: item for item in data["saldos"]}
    assert by_id[owner["user"]["id"]]["parte"] == 50
    assert by_id[owner["user"]["id"]]["saldo"] == -50
    assert by_id[partner["user"]["id"]]["parte"] == 50
    assert by_id[partner["user"]["id"]]["saldo"] == 50
    assert by_id[novo["user"]["id"]]["parte"] == 0
    assert by_id[novo["user"]["id"]]["saldo"] == 0
    assert len(data["transferencias"]) == 1
    assert data["transferencias"][0]["de_usuario_id"] == partner["user"]["id"]
    assert novo["user"]["id"] not in {
        data["transferencias"][0]["de_usuario_id"],
        data["transferencias"][0]["para_usuario_id"],
    }

    criada = add_activity(client, owner["headers"], obra["id"], nome="Depois", valor="90")
    atividades = client.get(f"/atividades?obra_id={obra['id']}", headers=owner["headers"])
    assert atividades.status_code == 200, atividades.text
    por_atividade = {item["id"]: item for item in atividades.json()}
    antiga = {item["usuario_id"] for item in por_atividade[activity["id"]]["participacao"]}
    nova = {item["usuario_id"] for item in por_atividade[criada["id"]]["participacao"]}
    assert antiga == {owner["user"]["id"], partner["user"]["id"]}
    assert nova == {owner["user"]["id"], partner["user"]["id"], novo["user"]["id"]}


def test_quem_paga_fora_da_participacao_fica_credor(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    activity = add_activity(client, owner["headers"], obra["id"], valor="100")
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    _pagar(client, partner["headers"], obra["id"], activity["id"], partner["user"]["id"], "40")

    data = _resumo(client, owner["headers"], obra["id"])
    assert data["restante"] == 60
    by_id = {item["usuario_id"]: item for item in data["saldos"]}
    assert by_id[owner["user"]["id"]]["parte"] == 40
    assert by_id[owner["user"]["id"]]["pago"] == 0
    assert by_id[owner["user"]["id"]]["saldo"] == 40
    assert by_id[partner["user"]["id"]]["parte"] == 0
    assert by_id[partner["user"]["id"]]["pago"] == 40
    assert by_id[partner["user"]["id"]]["saldo"] == -40
    assert data["transferencias"][0]["de_usuario_id"] == owner["user"]["id"]
    assert data["transferencias"][0]["para_usuario_id"] == partner["user"]["id"]
    assert data["transferencias"][0]["valor"] == 40


def test_membro_removido_continua_no_acerto(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    activity = add_activity(client, owner["headers"], obra["id"], valor="100")
    _pagar(client, partner["headers"], obra["id"], activity["id"], partner["user"]["id"], "100")
    removed = client.delete(f"/obras/{obra['id']}/membros/{partner['user']['id']}", headers=owner["headers"])
    assert removed.status_code == 200, removed.text

    data = _resumo(client, owner["headers"], obra["id"])
    by_id = {item["usuario_id"]: item for item in data["saldos"]}
    assert by_id[partner["user"]["id"]]["parte"] == 50
    assert by_id[partner["user"]["id"]]["pago"] == 100
    assert by_id[partner["user"]["id"]]["saldo"] == -50
    assert by_id[owner["user"]["id"]]["parte"] == 50
    assert by_id[owner["user"]["id"]]["saldo"] == 50
    assert data["transferencias"][0]["de_usuario_id"] == owner["user"]["id"]
    assert data["transferencias"][0]["para_usuario_id"] == partner["user"]["id"]
    assert data["transferencias"][0]["valor"] == 50


def test_editar_participacao_vale_so_para_a_atividade(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    first = add_activity(client, owner["headers"], obra["id"], nome="Primeira", valor="100")
    second = add_activity(client, owner["headers"], obra["id"], nome="Segunda", valor="80")
    edited = client.put(
        f"/edit-activity/{first['id']}?obra_id={obra['id']}",
        data={
            "participacao": json.dumps([{"usuario_id": owner["user"]["id"], "percentual": 100}]),
        },
        headers=owner["headers"],
    )
    assert edited.status_code == 200, edited.text
    atividades = client.get(f"/atividades?obra_id={obra['id']}", headers=owner["headers"])
    por_atividade = {item["id"]: item for item in atividades.json()}
    primeira = {item["usuario_id"]: item["percentual"] for item in por_atividade[first["id"]]["participacao"]}
    segunda = {item["usuario_id"] for item in por_atividade[second["id"]]["participacao"]}
    assert primeira == {owner["user"]["id"]: 100}
    assert segunda == {owner["user"]["id"], partner["user"]["id"]}


def test_participacao_soma_invalida(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    response = client.patch(
        f"/obras/{obra['id']}/participacao",
        json={
            "participantes": [
                {"usuario_id": owner["user"]["id"], "percentual": 60},
                {"usuario_id": partner["user"]["id"], "percentual": 30},
            ]
        },
        headers=owner["headers"],
    )
    assert response.status_code == 400


def test_membro_nao_altera_participacao_da_obra(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    response = client.patch(
        f"/obras/{obra['id']}/participacao",
        json={
            "participantes": [
                {"usuario_id": owner["user"]["id"], "percentual": 70},
                {"usuario_id": partner["user"]["id"], "percentual": 30},
            ]
        },
        headers=partner["headers"],
    )
    assert response.status_code == 403
