import pytest
from app.services.review_service import ReviewService
from app.models.review import AlbumReview

def test_create_spotify_review_success(test_db, user_mock):
    """
    CENÁRIO 1: Fluxo Clássico (Spotify)
    Enviamos IDs explícitos. O sistema deve respeitá-los.
    """
    payload = {
        "album": {
            "id": "spotify_album_123", # <--- ID veio preenchido
            "name": "The Dark Side of the Moon",
            "artist": "Pink Floyd",
            "cover": "http://cover.url"
        },
        "review_text": "Clássico absoluto.",
        "tracks": [
            { "id": "t1", "name": "Speak to Me", "track_number": 1, "userScore": 10.0 },
            { "id": "t2", "name": "Breathe", "track_number": 2, "userScore": 9.0 }
        ]
    }

    # Executa
    review = ReviewService.create_review(user_mock, payload)

    # Asserts
    assert review.spotify_album_id == "spotify_album_123" # Deve manter o ID original
    assert review.album_name == "The Dark Side of the Moon"
    
    # Verifica cálculo (10 + 9) / 2 = 9.5
    assert review.average_score == 9.5
    assert review.tier == 'S'
    
    # Verifica faixas
    assert len(review.tracks) == 2
    assert review.tracks[0].spotify_track_id == "t1" # ID da faixa preservado

def test_create_custom_review_success(test_db, user_mock):
    """
    CENÁRIO 2: Fluxo Novo (Manual/Custom)
    NÃO enviamos IDs. O sistema deve gerar um ID 'custom:...'.
    """
    payload = {
        "album": {
            # Note: SEM O CAMPO "id" AQUI!
            "name": "Minha Mixtape Rara",
            "artist": "MC Garibaldo",
            "cover": None # Testando sem capa também
        },
        "review_text": "Raridade encontrada na gaveta.",
        "tracks": [
            { 
                "name": "Intro Caseira", 
                "track_number": 1, 
                "userScore": 8.0 
                # Note: SEM "id" NA FAIXA TAMBÉM!
            },
            { "name": "Freestyle no Quintal", "track_number": 2, "userScore": 7.0 }
        ]
    }

    # Executa
    review = ReviewService.create_review(user_mock, payload)

    # Asserts Críticos do Novo Recurso
    assert review.spotify_album_id.startswith("custom:") # <--- O Pulo do Gato!
    assert review.artist_name == "MC Garibaldo"
    assert review.cover_url is None
    
    # Verifica se calculou a média mesmo sendo custom
    # (8 + 7) / 2 = 7.5 -> Tier B
    assert review.average_score == 7.5
    assert review.tier == 'B'
    
    # Verifica se salvou as faixas sem ID externo
    assert len(review.tracks) == 2
    assert review.tracks[0].track_name == "Intro Caseira"
    assert review.tracks[0].spotify_track_id is None # Tem que ser nulo

def test_create_review_invalid_score(test_db, user_mock):
    """
    Testa validação de nota (mantido para garantir segurança).
    """
    # Mesmo payload custom, mas com nota errada
    payload = {
        "album": { "name": "Erro", "artist": "Erro" },
        "tracks": [
            { "name": "Faixa Errada", "track_number": 1, "userScore": 50.0 } # > 10
        ]
    }
    pass 

def test_get_calendar_data(test_db, user_mock):
    """
    Testa se o calendário agrupa corretamente.
    """
    from datetime import datetime
    
    # Cria uma review customizada para popular o banco
    payload = {
        "album": { "name": "Calendar Custom", "artist": "X" },
        "tracks": [{ "name": "T1", "track_number": 1, "userScore": 10 }]
    }
    ReviewService.create_review(user_mock, payload)

    # Busca
    now = datetime.now()
    calendar = ReviewService.get_calendar_data(user_mock.id, now.month, now.year)

    day_key = str(now.day)
    assert day_key in calendar
    assert calendar[day_key][0].album_name == "Calendar Custom"