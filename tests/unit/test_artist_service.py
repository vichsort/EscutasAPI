import pytest
from unittest.mock import patch
from app.services.artist_service import ArtistService
from app.models.review import AlbumReview
from app.models.platinum import UserPlatinum
from app.models.user import User
from app.models.album import Album
from app.models.artist import Artist
from app.services.spotify_sync_service import SpotifySyncService

def _seed_discography(test_db, user_mock):
    """Popula banco com artista e 3 álbuns canônicos."""
    artist = Artist(
        spotify_artist_id="id_da_banda",
        name="Banda Teste",
        image_url="http://minha-imagem-falsa.com/foto.jpg"
    )
    test_db.session.add(artist)
    test_db.session.flush()

    for i in range(1, 4):
        test_db.session.add(Album(
            spotify_album_id=f"album_{i}",
            name=f"Estúdio {i}",
            clean_name=f"Estúdio {i}",
            artist_name="Banda Teste",
            artist_spotify_id="id_da_banda",
            release_date=f"202{i}-01-01",
            is_canonical=True
        ))

    test_db.session.commit()

@patch('app.services.artist_service.SpotifySyncService.sync_artist_discography')
def test_quase_platinar_artista(mock_sync, app, test_db, user_mock):
    """Usuário revisou 2 de 3 álbuns. Platina negada!"""
    with app.app_context():
        fresh_user = test_db.session.get(User, user_mock.id)
        _seed_discography(test_db, fresh_user)

        mock_sync.return_value = Artist.query.filter_by(spotify_artist_id="id_da_banda").first()

        r1 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_1", album_name="Estúdio 1", artist_name="Banda Teste")
        r2 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_2", album_name="Estúdio 2", artist_name="Banda Teste")
        test_db.session.add_all([r1, r2])
        test_db.session.commit()

        resultado = ArtistService.get_platinum_progress(fresh_user, "id_da_banda")

        assert resultado['stats']['is_platinum'] is False
        assert resultado['stats']['total_required'] == 3
        assert resultado['stats']['completed_count'] == 2

        medalha = test_db.session.query(UserPlatinum).filter_by(user_id=fresh_user.id).first()
        assert medalha is None

@patch('app.services.artist_service.SpotifySyncService.sync_artist_discography')
def test_platinar_artista_com_sucesso(mock_sync, app, test_db, user_mock):
    """Usuário revisou 3 de 3 álbuns. Platina concedida!"""
    with app.app_context():
        fresh_user = test_db.session.get(User, user_mock.id)
        _seed_discography(test_db, fresh_user)

        mock_sync.return_value = Artist.query.filter_by(spotify_artist_id="id_da_banda").first()

        r1 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_1", album_name="Estúdio 1", artist_name="Banda Teste")
        r2 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_2", album_name="Estúdio 2", artist_name="Banda Teste")
        r3 = AlbumReview(user_id=fresh_user.id, spotify_album_id="album_3", album_name="Estúdio 3", artist_name="Banda Teste")
        test_db.session.add_all([r1, r2, r3])
        test_db.session.commit()

        resultado = ArtistService.get_platinum_progress(fresh_user, "id_da_banda")

        assert resultado['stats']['is_platinum'] is True
        assert resultado['stats']['completed_count'] == 3

        medalha = test_db.session.query(UserPlatinum).filter_by(user_id=fresh_user.id).first()
        assert medalha is not None
        assert medalha.artist_name == "Banda Teste"