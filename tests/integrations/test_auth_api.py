import pytest
from unittest.mock import patch, MagicMock
from app.models.user import User

def test_login_redirect(client):
    """
    Testa GET /api/login
    Deve redirecionar (302) para a URL do Spotify.
    """
    # Mockamos o método que gera a URL para não precisar de credenciais reais
    with patch('spotipy.oauth2.SpotifyOAuth.get_authorize_url') as mock_url:
        mock_url.return_value = "https://accounts.spotify.com/authorize?fake=123"
        
        response = client.get('/api/login')
        
        # 302 = Redirect
        assert response.status_code == 302
        # Verifica se estamos sendo enviados para o lugar certo
        assert "https://accounts.spotify.com" in response.headers["Location"]

def test_callback_success(client, test_db):
    """
    Testa GET /api/callback
    Simula o retorno do Spotify com um código válido.
    Deve criar o usuário no banco e logar na sessão.
    """
    # Mocks para enganar o fluxo OAuth
    mock_token_info = {
        'access_token': 'fake_access_token',
        'refresh_token': 'fake_refresh_token',
        'expires_at': 9999999999,
        'scope': 'user-read-private'
    }
    
    mock_spotify_user = {
        'id': 'new_user_123',
        'display_name': 'New User',
        'email': 'new@test.com',
        'images': []
    }

    # A troca do Código pelo Token
    with patch('spotipy.oauth2.SpotifyOAuth.get_access_token', return_value=mock_token_info):
        # A busca dos dados do usuário (sp.current_user())
        with patch('spotipy.Spotify.current_user', return_value=mock_spotify_user):
            
            # Chama a rota como se fosse o Spotify devolvendo o usuário
            response = client.get('/api/callback?code=fake_auth_code')

            assert response.status_code in [200, 302] 
            
            # VERIFICAÇÃO PRINCIPAL: O usuário foi criado no banco?
            user = test_db.session.query(User).filter_by(spotify_id='new_user_123').first()
            assert user is not None
            assert user.display_name == 'New User'
            
            # Verifica se a sessão foi criada
            with client.session_transaction() as sess:
                assert sess['user_id'] == str(user.id)

def test_logout(client, user_mock):
    """
    Testa GET /api/logout
    Deve limpar a sessão.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id

    response = client.get('/api/logout')
    
    assert response.status_code == 200

    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_get_me_endpoint(client, user_mock):
    """
    Testa GET /api/me (Endpoint que o frontend chama ao carregar)
    """
    # Sem login -> Erro
    resp_anon = client.get('/api/me')
    assert resp_anon.status_code in [401, 302]
    
    # Com login -> Sucesso
    with client.session_transaction() as sess:
        sess['user_id'] = user_mock.id
        
    resp_auth = client.get('/api/me')
    assert resp_auth.status_code == 200
    assert resp_auth.json['data']['spotify_id'] == user_mock.spotify_id