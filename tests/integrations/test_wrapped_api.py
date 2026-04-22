import pytest
from datetime import datetime
from app.models import User, AlbumReview, BlogPost

def test_gerar_wrapped_com_sucesso(auth_client, mock_spotify, test_db):
    """
    Testa o caminho feliz: o usuário tem reviews, o Spotify responde,
    a playlist é gerada e o rascunho do blog é salvo no banco!
    """
    # ---------------------------------------------------------
    # 1. PREPARANDO O BANCO DE DADOS
    # ---------------------------------------------------------
    # Pegamos o usuário logado que a fixture 'auth_client' usou
    user = test_db.session.query(User).first()
    
    # Injetamos reviews no mês de Abril (4) de 2026
    r1 = AlbumReview(
        user_id=user.id,
        spotify_album_id="album_top_id",
        album_name="Random Access Memories",
        artist_name="Daft Punk",
        average_score=5.0,
        created_at=datetime(2026, 4, 10)
    )
    r2 = AlbumReview(
        user_id=user.id,
        spotify_album_id="album_mediano_id",
        album_name="Álbum Mediano",
        artist_name="Artista Mediano",
        average_score=3.5,
        created_at=datetime(2026, 4, 20)
    )
    test_db.session.add_all([r1, r2])
    test_db.session.commit()

    # ---------------------------------------------------------
    # 2. PREPARANDO O MOCK DO SPOTIFY
    # ---------------------------------------------------------
    fake_sp = mock_spotify.return_value
    
    # Simulando a resposta para o sp.album (Álbum de Ouro)
    fake_sp.album.return_value = {
        'name': 'Random Access Memories',
        'artists': [{'name': 'Daft Punk'}],
        'images': [{'url': 'http://capa-daftpunk.jpg'}]
    }
    
    # Simulando a resposta para o sp.album_tracks (Músicas da Playlist)
    fake_sp.album_tracks.return_value = {
        'items': [{'uri': 'spotify:track:getlucky123'}]
    }
    
    # Simulando a criação da Playlist
    fake_sp.user_playlist_create.return_value = {
        'id': 'minha_playlist_de_abril'
    }
    
    # Simulando a adição de músicas na playlist
    fake_sp.playlist_add_items.return_value = True

    # ---------------------------------------------------------
    # 3. DISPARANDO A REQUISIÇÃO (O GATILHO)
    # ---------------------------------------------------------
    payload = {"month": 4, "year": 2026}
    response = auth_client.post('/api/wrapped/generate-monthly', json=payload)
    data = response.get_json()

    # ---------------------------------------------------------
    # 4. ASSERTS: VERIFICANDO SE A HYDRA FUNCIONOU
    # ---------------------------------------------------------
    assert response.status_code == 200
    assert "gerado com sucesso" in response.get_json()['message']
    
    # Verificando as chaves de retorno
    post_id = data['data']['post_id']
    playlist_url = data['data']['playlist_url']
    
    assert playlist_url == "https://open.spotify.com/playlist/minha_playlist_de_abril"

    # Indo direto no banco para garantir que o rascunho do Blog está perfeito!
    post_criado = test_db.session.get(BlogPost, post_id)
    
    assert post_criado is not None
    assert post_criado.status == 'DRAFT'
    assert "Abril" in post_criado.title
    assert "Random Access Memories" in post_criado.content # O texto foi injetado!
    assert post_criado.cover_image_url == "http://capa-daftpunk.jpg"


def test_gerar_wrapped_sem_reviews_retorna_erro(auth_client):
    """
    Se o usuário tentar gerar um Wrapped para um mês em que
    ele não ouviu nada, o sistema deve barrar educadamente.
    """
    # Tentando gerar para um mês no futuro sem dados
    payload = {"month": 12, "year": 2099}
    response = auth_client.post('/api/wrapped/generate-monthly', json=payload)
    
    assert response.status_code == 400