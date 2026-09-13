from tests.conftest import add_activity, create_obra, invite_and_accept, register_and_login


def test_resumo_agregado_e_saldos(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    activity = add_activity(client, owner["headers"], obra["id"], valor="100")
    partner = invite_and_accept(client, owner["headers"], obra["id"], "membro")
    payment = client.post(
        f"/register-payment?obra_id={obra['id']}",
        data={
            "atividade_id": activity["id"],
            "usuario_id": owner["user"]["id"],
            "value": "100",
        },
        headers=owner["headers"],
    )
    assert payment.status_code == 200, payment.text

    resumo = client.get(f"/obras/{obra['id']}/resumo", headers=owner["headers"])
    assert resumo.status_code == 200, resumo.text
    data = resumo.json()
    assert data["total"] == 100
    assert data["total_pago"] == 100
    assert data["restante"] == 0
    assert len(data["saldos"]) == 2
    by_id = {item["usuario_id"]: item for item in data["saldos"]}
    owner_saldo = by_id[owner["user"]["id"]]
    partner_saldo = by_id[partner["user"]["id"]]
    assert owner_saldo["cota"] == 50
    assert owner_saldo["pago"] == 100
    assert owner_saldo["saldo"] == -50
    assert partner_saldo["cota"] == 50
    assert partner_saldo["pago"] == 0
    assert partner_saldo["saldo"] == 50


def test_resumo_nao_membro(client):
    owner = register_and_login(client)
    obra = create_obra(client, owner["headers"])
    outsider = register_and_login(client)
    response = client.get(f"/obras/{obra['id']}/resumo", headers=outsider["headers"])
    assert response.status_code == 403
