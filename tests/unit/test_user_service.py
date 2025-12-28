from app.services.user_service import UserService
from app.schemas.user import UserPublic

def test_search_user_by_name(test_db, user_mock):
    """
    Deve encontrar o usuário pelo nome parcial.
    """
    # Action
    results = UserService.search_users("Tracie")
    
    # Assert
    assert len(results) == 1
    assert results[0].display_name == "Tracie Tester"
    assert isinstance(results[0], UserPublic) # Garante que estamos usando Pydantic

def test_search_user_not_found(test_db):
    """
    Deve retornar lista vazia se não achar ninguém.
    """
    results = UserService.search_users("Fantasma")
    assert len(results) == 0
    assert results == []

def test_get_user_profile(test_db, user_mock):
    """
    Deve retornar o perfil completo via UUID.
    """
    # Action
    # user_mock.id é um UUID object, convertemos pra str pq o service espera str (via URL)
    profile = UserService.get_user_profile(str(user_mock.id))
    
    # Assert
    assert profile is not None
    assert profile.spotify_id == "tracie_test"
    assert profile.joined_at is not None # Verifica se a formatação de data funcionou