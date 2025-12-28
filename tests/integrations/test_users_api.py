import pytest
import uuid

def test_search_users_api_success(client, user_mock):
    """
    Testa GET /api/users/search
    Deve encontrar o usuário pelo nome.
    """
    # 1. Login (Simulação de Sessão)
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id

    # 2. Busca por "Tracie" (Nome do user_mock existente no seu conftest)
    # CORREÇÃO: Buscamos "Tracie" em vez de "Integration"
    response = client.get('/api/users/search?q=Tracie')

    # 3. Asserts
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    
    data = response.json['data']
    assert isinstance(data, list)
    
    # Agora deve passar, pois Tracie existe
    assert len(data) >= 1
    assert data[0]['display_name'] == "Tracie Tester"
    # Verifica se serializou o UUID corretamente
    assert data[0]['id'] == str(user_mock.id)

def test_search_users_validation_error(client, user_mock):
    """
    Testa validação: Query muito curta deve dar erro 400.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id

    # Busca com apenas 1 caractere
    response = client.get('/api/users/search?q=a')

    assert response.status_code == 400
    assert "pelo menos 2 caracteres" in response.json['message']

def test_get_profile_api_success(client, user_mock):
    """
    Testa GET /api/users/<uuid>
    Deve retornar os detalhes do perfil.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id

    # Busca o próprio perfil
    response = client.get(f'/api/users/{user_mock.id}')

    assert response.status_code == 200
    data = response.json['data']
    
    # CORREÇÃO: Verifica o ID correto da Tracie
    assert data['spotify_id'] == "tracie_test"
    assert 'joined_at' in data 

def test_get_profile_not_found(client, user_mock):
    """
    Testa erro 404 ao buscar usuário inexistente.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id

    # Gera um UUID aleatório que não existe no banco
    random_uuid = str(uuid.uuid4())
    response = client.get(f'/api/users/{random_uuid}')

    assert response.status_code == 404
    assert "não encontrado" in response.json['message']