import pytest
from unittest.mock import MagicMock
from app.services.custom_album_service import CustomAlbumService
from app.exceptions import ResourceNotFoundError

def test_create_custom_album_sucesso(app, test_db, user_mock):
    """Cria um álbum customizado com tracks e verifica o output."""
    with app.app_context():
        payload = MagicMock()
        payload.name = "Álbum Caseiro"
        payload.artist_name = "Banda do Quintal"
        payload.cover_url = "https://exemplo.com/capa.jpg"
        payload.tracks = [
            MagicMock(name="Faixa 1", track_number=1, duration_ms=200000),
            MagicMock(name="Faixa 2", track_number=2, duration_ms=180000),
        ]
        # Corrige o .name do MagicMock que é reservado
        payload.tracks[0].name = "Faixa 1"
        payload.tracks[1].name = "Faixa 2"

        result = CustomAlbumService.create_custom_album(user_mock, payload)

        assert result.name == "Álbum Caseiro"
        assert result.artist_name == "Banda do Quintal"
        assert result.spotify_album_id.startswith("custom:")
        assert len(result.tracks) == 2

def test_create_custom_album_sem_tracks(app, test_db, user_mock):
    """Cria álbum sem tracks — deve funcionar normalmente."""
    with app.app_context():
        payload = MagicMock()
        payload.name = "Álbum Vazio"
        payload.artist_name = "Artista Solo"
        payload.cover_url = None
        payload.tracks = []

        result = CustomAlbumService.create_custom_album(user_mock, payload)

        assert result.name == "Álbum Vazio"
        assert result.tracks == []

def test_get_custom_album_sucesso(app, test_db, user_mock):
    """Cria e depois busca pelo custom:uuid — deve retornar AlbumFull."""
    with app.app_context():
        payload = MagicMock()
        payload.name = "Álbum Buscável"
        payload.artist_name = "Artista X"
        payload.cover_url = None
        payload.tracks = [MagicMock(track_number=1, duration_ms=150000)]
        payload.tracks[0].name = "Única Faixa"

        created = CustomAlbumService.create_custom_album(user_mock, payload)
        result = CustomAlbumService.get_custom_album(created.spotify_album_id)

        assert result.name == "Álbum Buscável"
        assert result.id == created.spotify_album_id
        assert result.total_tracks == 1

def test_get_custom_album_id_invalido(app, test_db):
    """ID malformado deve lançar ResourceNotFoundError."""
    with app.app_context():
        with pytest.raises(ResourceNotFoundError):
            CustomAlbumService.get_custom_album("custom:isso-nao-e-uuid")

def test_get_custom_album_nao_existe(app, test_db):
    """UUID válido mas inexistente deve lançar ResourceNotFoundError."""
    with app.app_context():
        with pytest.raises(ResourceNotFoundError):
            CustomAlbumService.get_custom_album("custom:00000000-0000-0000-0000-000000000000")