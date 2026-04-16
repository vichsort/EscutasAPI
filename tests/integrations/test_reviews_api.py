import pytest

def test_criar_review_sucesso_absoluto(auth_client):
    """
    O Caminho Feliz: Testa se um payload perfeito cria a review e calcula a média.
    """
    payload = {
        "album": {
            "name": "O Rappa - Lado B Lado A",
            "artist": "O Rappa",
            "id": "fake_spotify_id"
        },
        "tracks": [
            {"name": "Tribunal de Rua", "track_number": 1, "userScore": 10},
            # Nota 9.5 (Float) para garantir que o Pydantic entende
            {"name": "Me Deixa", "track_number": 2, "userScore": 9.5} 
        ],
        "review_text": "Clássico absoluto do rock nacional!",
        "listened_date": "15/04/2026"
    }

    # Fazemos um POST real na rota, como se fôssemos o Frontend
    response = auth_client.post('/api/reviews', json=payload)
    
    assert response.status_code == 201
    
    data = response.get_json()['data']
    assert data['album_name'] == "O Rappa - Lado B Lado A"
    assert data['average_score'] == 9.8  # (10 + 9.5) / 2 = 9.75 -> arredonda
    assert data['tier'] == "S"  # Média 9.75 é Tier S automático!

def test_criar_review_nota_invalida_barrado_pelo_pydantic(auth_client):
    """
    Tenta hackear a API enviando uma nota 15 para uma faixa.
    O banco de dados nunca pode ver isso.
    """
    payload = {
        "album": {"name": "Hacker Album", "artist": "Mr Robot"},
        "tracks": [
            {"name": "Faixa 1", "track_number": 1, "userScore": 15} # <-- Nota maior que 10!
        ]
    }

    response = auth_client.post('/api/reviews', json=payload)
    
    # O Pydantic deve devolver um Bad Request (400)
    assert response.status_code == 400
    
    # A mensagem de erro deve conter algo reclamando da validação
    resposta_json = str(response.get_json()).lower()
    assert "validation error" in resposta_json or "userscore" in resposta_json

def test_criar_review_todas_faixas_ignoradas(auth_client):
    """
    Testa a nossa regra de negócio customizada (o @model_validator).
    Não faz sentido avaliar um álbum e ignorar 100% das faixas.
    """
    payload = {
        "album": {"name": "Álbum Chato", "artist": "Banda Chata"},
        "tracks": [
            {"name": "Faixa 1", "track_number": 1, "is_ignored": True},
            {"name": "Faixa 2", "track_number": 2, "is_ignored": True}
        ]
    }

    response = auth_client.post('/api/reviews', json=payload)
    
    assert response.status_code == 400
    
    # A mensagem de erro exata que nós escrevemos no schema
    mensagem = response.get_json().get('message', '').lower()
    assert "pelo menos uma" in mensagem or "valida" in mensagem