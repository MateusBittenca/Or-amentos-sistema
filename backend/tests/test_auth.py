from tests.conftest import register_and_login


def test_login_sucesso(client):
    session = register_and_login(client)
    obras = client.get("/obras", headers=session["headers"])
    assert obras.status_code == 200
    assert isinstance(obras.json(), list)


def test_login_senha_errada(client):
    session = register_and_login(client)
    response = client.post("/token", data={"username": session["email"], "password": "errada"})
    assert response.status_code == 401


def test_obras_sem_token(client):
    response = client.get("/obras")
    assert response.status_code == 401


def test_password_reset_indisponivel(client):
    response = client.post("/password/request-reset", json={"username": "alguem@test.local"})
    assert response.status_code == 503
    reset = client.post(
        "/password/reset",
        json={"username": "alguem@test.local", "reset_token": "x", "new_password": "nova1234"},
    )
    assert reset.status_code == 503
