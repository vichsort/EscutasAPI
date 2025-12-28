from unittest.mock import MagicMock, patch
from app.services.album_service import AlbumService
from app.schemas.album import AlbumBase, AlbumFull

# Dados Falsos que simulam a resposta crua do Spotify
MOCK_SPOTIFY_SEARCH = {
    'albums': {
        'items': [
            {
                'id': '123',
                'name': 'Mock Album',
                'album_type': 'album',
                'artists': [{'name': 'Mock Artist'}],
                'images': [{'url': 'http://cover.jpg'}],
                'release_date': '2025-01-01'
            }
        ]
    }
}

def test_search_albums_success(user_mock):
    """
    Deve buscar no Spotify (mockado) e converter para lista de AlbumBase (Pydantic).
    """
    # O 'patch' intercepta a chamada ao SpotifyService.get_client
    # e substitui por um objeto falso que nós controlamos.
    with patch('app.services.album_service.SpotifyService.get_client') as mock_get_client:
        
        # Configura o cliente falso do Spotify
        mock_sp_client = MagicMock()
        mock_sp_client.search.return_value = MOCK_SPOTIFY_SEARCH
        mock_get_client.return_value = mock_sp_client

        # Executa o Serviço
        results = AlbumService.search_albums(user_mock, "query")

        # Asserts
        assert len(results) == 1
        assert isinstance(results[0], AlbumBase)
        assert results[0].name == "Mock Album"
        assert results[0].artist == "Mock Artist"
        
        # Verifica se o serviço realmente chamou o 'search' do Spotify
        mock_sp_client.search.assert_called_once()

def test_search_albums_empty(user_mock):
    """
    Se o Spotify não retornar nada, deve retornar lista vazia.
    """
    with patch('app.services.album_service.SpotifyService.get_client') as mock_get_client:
        mock_sp = MagicMock()
        mock_sp.search.return_value = {'albums': {'items': []}}
        mock_get_client.return_value = mock_sp

        results = AlbumService.search_albums(user_mock, "nada consta")
        
        assert results == []