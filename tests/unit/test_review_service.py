import pytest
from datetime import datetime
from app.services.review_service import ReviewService
from app.utils.response_util import APIError
from app.schemas.review import ReviewFull

def test_create_review_success(test_db, user_mock):
    """
    Testa o fluxo feliz: Criar review válida, calcular média e retornar Schema.
    """
    # Payload simulando o Frontend
    payload = {
        "album": {
            "id": "spotify_album_123",
            "name": "Dark Side of the Moon",
            "artist": "Pink Floyd",
            "cover": "http://cover.url"
        },
        "review_text": "Album excelente.",
        "tracks": [
            { "id": "t1", "name": "Speak to Me", "track_number": 1, "userScore": 10.0 },
            { "id": "t2", "name": "Breathe", "track_number": 2, "userScore": 8.0 }
        ]
    }

    result = ReviewService.create_review(user_mock, payload)

    assert isinstance(result, ReviewFull)
    assert result.album_name == "Dark Side of the Moon"
    assert len(result.tracks) == 2
    
    # Verifica a Regra de Negócio (Cálculo de Média)
    # Média: (10 + 8) / 2 = 9.0
    assert result.average_score == 9.0
    
    # Verifica a Regra de Tier
    # >= 8.5 e < 9.5 deve ser Tier 'A'
    assert result.tier == 'A'

def test_create_review_invalid_score(test_db, user_mock):
    """
    Deve lançar APIError se a nota for maior que 10.
    """
    payload = {
        "album": { "id": "1", "name": "X", "artist": "Y", "cover": "Z" },
        "tracks": [
            { "id": "t1", "name": "Faixa Ruim", "track_number": 1, "userScore": 11.0 }
        ]
    }

    # Verifica se a exceção é lançada
    with pytest.raises(APIError) as excinfo:
        ReviewService.create_review(user_mock, payload)
    
    assert "Nota inválida" in str(excinfo.value)

def test_get_calendar_data(test_db, user_mock):
    """
    Deve retornar as reviews organizadas por dia.
    """
    # Cria uma review para garantir que o banco não está vazio
    payload = {
        "album": { "id": "cal_1", "name": "Calendar Album", "artist": "X", "cover": "Y" },
        "tracks": [{ "id": "t1", "name": "F1", "track_number": 1, "userScore": 10 }]
    }
    ReviewService.create_review(user_mock, payload)

    # Busca o calendário do mês atual
    now = datetime.now()
    calendar = ReviewService.get_calendar_data(user_mock.id, now.month, now.year)

    # Verifica
    day_key = str(now.day)
    assert day_key in calendar
    assert len(calendar[day_key]) == 1
    assert calendar[day_key][0].album_name == "Calendar Album"