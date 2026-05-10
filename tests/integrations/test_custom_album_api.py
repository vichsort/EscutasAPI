import pytest

def test_criar_custom_album_sucesso(auth_client):
    """Caminho feliz — cria álbum com tracks."""
    payload = {
        "name": "Álbum da Garagem",
        "artist_name": "Banda Caseira",
        "cover_url": "https://exemplo.com/capa.jpg",
        "tracks": [
            {"name": "Abertura", "track_number": 1, "duration_ms": 120000},
            {"name": "Encerramento", "track_number": 2, "duration_ms": 180000}
        ]
    }

    response = auth_client.post('/api/albums/custom', json=payload)

    assert response.status_code == 201
    data = response.get_json()['data']
    assert data['name'] == "Álbum da Garagem"
    assert data['spotify_album_id'].startswith("custom:")
    assert len(data['tracks']) == 2

def test_criar_custom_album_sem_tracks(auth_client):
    """Álbum sem tracks é válido."""
    payload = {
        "name": "Álbum Minimalista",
        "artist_name": "Artista Zen"
    }

    response = auth_client.post('/api/albums/custom', json=payload)

    assert response.status_code == 201
    data = response.get_json()['data']
    assert data['tracks'] == []

def test_criar_custom_album_cover_url_invalida(auth_client):
    """URL de capa inválida deve ser barrada pelo Pydantic."""
    payload = {
        "name": "Álbum Suspeito",
        "artist_name": "Hacker",
        "cover_url": "javascript:alert(1)"
    }

    response = auth_client.post('/api/albums/custom', json=payload)
    assert response.status_code == 400

def test_criar_custom_album_sem_autenticacao(client):
    """Sem JWT deve retornar 401."""
    payload = {
        "name": "Álbum Anônimo",
        "artist_name": "Sem Usuário"
    }

    response = client.post('/api/albums/custom', json=payload)
    assert response.status_code == 401

def test_criar_custom_album_nome_ausente(auth_client):
    """Payload sem nome deve ser barrado."""
    payload = {
        "artist_name": "Artista Sem Nome"
    }

    response = auth_client.post('/api/albums/custom', json=payload)
    assert response.status_code == 400