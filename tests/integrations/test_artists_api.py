from unittest.mock import patch


def test_busca_artistas_sem_usuario_no_service_funciona(auth_client, mock_spotify):
    fake_sp = mock_spotify.return_value
    fake_sp.search.return_value = {'artists': {'items': []}}

    with patch('app.services.spotify_service.SpotifyService.maybe_refresh_token'):
        response = auth_client.get('/api/artists/search?q=artista_inexistente')

    assert response.status_code == 200
    assert response.get_json()['data'] == []
