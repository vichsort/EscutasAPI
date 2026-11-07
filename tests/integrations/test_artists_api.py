from unittest.mock import patch

from app.exceptions import SpotifyRateLimitError


def test_busca_artistas_com_cota_estourada_retorna_503(auth_client, mock_spotify):
    fake_sp = mock_spotify.return_value
    fake_sp.search.side_effect = SpotifyRateLimitError(quota_exceeded=True, retry_after=120)

    with patch('app.services.spotify_service.SpotifyService.maybe_refresh_token'):
        response = auth_client.get('/api/artists/search?q=cota_estourada')

    assert response.status_code == 503
    body = response.get_json()
    assert body['status'] == 'error'
    assert body['retry_after'] == 120


def test_busca_artistas_sem_usuario_no_service_funciona(auth_client, mock_spotify):
    fake_sp = mock_spotify.return_value
    fake_sp.search.return_value = {'artists': {'items': []}}

    with patch('app.services.spotify_service.SpotifyService.maybe_refresh_token'):
        response = auth_client.get('/api/artists/search?q=artista_inexistente')

    assert response.status_code == 200
    assert response.get_json()['data'] == []
