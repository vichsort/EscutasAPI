import pytest
from unittest.mock import MagicMock, patch
from app.services.spotify_sync_service import SpotifySyncService
from app.models.artist import Artist
from app.models.album import Album
from app.exceptions import SpotifyAPIError

def _fake_artist_data():
    return {
        'id': 'artist_123',
        'name': 'Artista Teste',
        'images': [{'url': 'https://img.com/a.jpg'}],
        'genres': ['rock', 'progressive rock']
    }

def _fake_album_data():
    return {
        'id': 'album_123',
        'name': 'Álbum Teste',
        'artists': [{'id': 'artist_123', 'name': 'Artista Teste'}],
        'images': [{'url': 'https://img.com/b.jpg'}],
        'release_date': '1973-03-01',
        'total_tracks': 2,
        'tracks': {
            'items': [
                {'id': 'track_1', 'name': 'Faixa 1', 'track_number': 1, 'duration_ms': 100000, 'preview_url': None},
                {'id': 'track_2', 'name': 'Faixa 2', 'track_number': 2, 'duration_ms': 200000, 'preview_url': None},
            ],
            'next': None
        }
    }

def test_sync_artist_cria_novo(app, test_db):
    """Artista inexistente no banco deve ser criado."""
    with app.app_context():
        sp = MagicMock()
        sp.artist.return_value = _fake_artist_data()

        artist = SpotifySyncService.sync_artist('artist_123', sp)

        assert artist.name == 'Artista Teste'
        assert artist.genres == ['rock', 'progressive rock']
        assert Artist.query.filter_by(spotify_artist_id='artist_123').first() is not None

def test_sync_artist_nao_rebusca_se_fresco(app, test_db):
    """Artista fresco no banco não deve ir ao Spotify."""
    with app.app_context():
        sp = MagicMock()
        sp.artist.return_value = _fake_artist_data()

        # Primeira sync
        SpotifySyncService.sync_artist('artist_123', sp)
        assert sp.artist.call_count == 1

        # Segunda sync — banco fresco, não deve chamar o Spotify
        SpotifySyncService.sync_artist('artist_123', sp)
        assert sp.artist.call_count == 1

def test_sync_album_cria_com_tracks(app, test_db):
    """Álbum inexistente deve ser criado com suas tracks."""
    with app.app_context():
        sp = MagicMock()
        sp.album.return_value = _fake_album_data()

        album = SpotifySyncService.sync_album('album_123', sp)

        assert album.name == 'Álbum Teste'
        assert Album.query.filter_by(spotify_album_id='album_123').first() is not None

def test_sync_artist_erro_spotify_faz_rollback(app, test_db):
    """Erro no Spotify deve fazer rollback e lançar SpotifyAPIError."""
    with app.app_context():
        sp = MagicMock()
        sp.artist.side_effect = Exception("Spotify caiu")

        with pytest.raises(SpotifyAPIError):
            SpotifySyncService.sync_artist('artist_erro', sp)