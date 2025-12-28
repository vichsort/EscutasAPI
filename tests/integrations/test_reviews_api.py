import pytest
from flask import session

def test_create_review_api_success(client, user_mock):
    """
    Testa o endpoint POST /api/reviews
    Deve criar a review e retornar 201 com JSON formatado.
    """
    # 1. SIMULAR LOGIN (O Pulo do Gato 🐱)
    # Acessamos a sessão do cliente de testes e forçamos o user_id
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id
        sess['user_uuid'] = str(user_mock.id) # Depende de como seu auth checa

    # 2. Payload (O que o Frontend enviaria)
    payload = {
        "album": {
            "id": "abc_123",
            "name": "Integration Test Album",
            "artist": "Pytest Band",
            "cover": "http://img.com"
        },
        "review_text": "Testando a rota HTTP.",
        "tracks": [
            { "id": "t1", "name": "Hit 1", "track_number": 1, "userScore": 9.5 }
        ]
    }

    # 3. Faz a requisição HTTP POST
    response = client.post('/api/reviews', json=payload)

    # 4. Asserts HTTP
    assert response.status_code == 201
    assert response.json['status'] == 'success'
    
    # Verifica se os dados voltaram (Pydantic serialization check)
    data = response.json['data']
    assert data['album_name'] == "Integration Test Album"
    assert data['tier'] == 'S' # 9.5 é Tier S

def test_get_history_api(client, user_mock):
    """
    Testa GET /api/reviews/history
    """
    # 1. Login
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id

    # 2. Chama a rota
    response = client.get('/api/reviews/history')

    # 3. Asserts
    assert response.status_code == 200
    assert 'data' in response.json
    assert 'meta' in response.json # Garante que a paginação funcionou

def test_unauthorized_access(client):
    """
    Testa se a API bloqueia quem não está logado.
    """
    # NÃO fazemos login aqui intencionalmente
    
    response = client.get('/api/reviews/history')
    
    # Deve retornar 401 (Unauthorized) ou 302 (Redirect) dependendo da sua config
    # Geralmente APIs retornam 401
    assert response.status_code in [401, 302]