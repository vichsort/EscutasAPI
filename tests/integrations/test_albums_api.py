from unittest.mock import patch
from app.schemas.album import AlbumBase

def test_search_albums_api_success(client, user_mock):
    """
    Testa GET /api/albums/search?q=Pink
    Usa MOCK para não chamar o Spotify de verdade.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id

    # Dados Falsos que o Service "retornaria"
    fake_albums = [
        AlbumBase(
            spotify_id="123", 
            name="Mocked Album", 
            artist="Mocked Artist", 
            cover_url="http://fake.url"
        )
    ]

    with patch('app.services.album_service.AlbumService.search_albums') as mock_service:
        mock_service.return_value = fake_albums

        response = client.get('/api/albums/search?q=Pink')

        assert response.status_code == 200
        assert response.json['status'] == 'success'
        
        data = response.json['data']
        assert len(data) == 1
        assert data[0]['name'] == "Mocked Album"
        assert data[0]['artist'] == "Mocked Artist"

def test_search_albums_missing_query(client, user_mock):
    """
    Testa validação: Se não enviar '?q=', deve retornar erro.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id

    response = client.get('/api/albums/search') # Sem query param

    assert response.status_code == 400
    assert "O termo de busca 'q' é obrigatório" in response.json['message']

def test_search_albums_unauthorized(client):
    """
    Testa segurança: Sem login, não pode buscar.
    """
    response = client.get('/api/albums/search?q=Test')
    
    assert response.status_code == 401