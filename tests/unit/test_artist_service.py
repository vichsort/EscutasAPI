import pytest
from unittest.mock import patch, MagicMock
from app.services.artist_service import ArtistService
from app.models.review import AlbumReview
from app.models.platinum import UserPlatinum
from app.models.user import User

# O Perfil Falso do Artista
MOCK_ARTIST_INFO = {
    "id": "id_da_banda",
    "name": "Banda Teste",
    "images": [{"url": "http://minha-imagem-falsa.com/foto.jpg"}]
}

# O Catálogo Falso do artista
MOCK_CATALOGO_SPOTIFY = {
    "items": [
        {
            "id": "album_1", "name": "Estúdio 1", "album_group": "album", "album_type": "album",
            "release_date": "2020-01-01", "images": [{"url": "capa1.jpg"}]
        },
        {
            "id": "album_2", "name": "Estúdio 2", "album_group": "album", "album_type": "album",
            "release_date": "2021-01-01", "images": [{"url": "capa2.jpg"}]
        },
        {
            "id": "album_3", "name": "Estúdio 3", "album_group": "album", "album_type": "album",
            "release_date": "2022-01-01", "images": [{"url": "capa3.jpg"}]
        }
    ],
    "next": None  # Para a paginação parar
}

@patch('app.services.artist_service.SpotifyService.get_client')
def test_quase_platinar_artista(mock_get_client, app, test_db, user_mock):
    """Usuário revisou 2 de 3 álbuns. Platina negada!"""
    
    # Criamos o nosso robô falso do Spotipy
    mock_sp = MagicMock()
    mock_sp.artist.return_value = MOCK_ARTIST_INFO
    mock_sp.artist_albums.return_value = MOCK_CATALOGO_SPOTIFY 
    mock_get_client.return_value = mock_sp

    with app.app_context():
        fresh_user = test_db.session.get(User, user_mock.id)

        # Inserimos DUAS reviews
        r1 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_1", album_name="Estúdio 1", artist_name="Banda Teste")
        r2 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_2", album_name="Estúdio 2", artist_name="Banda Teste")
        test_db.session.add_all([r1, r2])
        test_db.session.commit()

        # Chamamos o Servica
        resultado = ArtistService.get_platinum_progress(fresh_user, "id_da_banda")

        # Verifica a matemática
        assert resultado['stats']['is_platinum'] is False
        assert resultado['stats']['total_required'] == 3
        assert resultado['stats']['completed_count'] == 2
        
        # Garante que a medalha NÃO existe no banco
        medalha = test_db.session.query(UserPlatinum).filter_by(user_id=fresh_user.id).first()
        assert medalha is None


@patch('app.services.artist_service.SpotifyService.get_client')
def test_platinar_artista_com_sucesso(mock_get_client, app, test_db, user_mock):
    """Usuário revisou 3 de 3 álbuns. Platina concedida!"""
    
    # Configuramos o robô falso novamente
    mock_sp = MagicMock()
    mock_sp.artist.return_value = MOCK_ARTIST_INFO
    mock_sp.artist_albums.return_value = MOCK_CATALOGO_SPOTIFY
    mock_get_client.return_value = mock_sp

    with app.app_context():
        fresh_user = test_db.session.get(User, user_mock.id)

        # Inserimos as TRÊS reviews
        r1 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_1", album_name="Estúdio 1", artist_name="Banda Teste")
        r2 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_2", album_name="Estúdio 2", artist_name="Banda Teste")
        r3 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_3", album_name="Estúdio 3", artist_name="Banda Teste")
        test_db.session.add_all([r1, r2, r3])
        test_db.session.commit()

        # Chamamos o Service
        resultado = ArtistService.get_platinum_progress(fresh_user, "id_da_banda")

        # Verifica as estatísticas do sucesso
        assert resultado['stats']['is_platinum'] is True
        assert resultado['stats']['completed_count'] == 3
        
        # a medalha FOI criada no banco?
        medalha = test_db.session.query(UserPlatinum).filter_by(user_id=fresh_user.id).first()
        assert medalha is not None
        assert medalha.artist_name == "Banda Teste"