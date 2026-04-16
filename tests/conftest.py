import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.extensions import db
from app.models.user import User

@pytest.fixture(scope='module')
def app():
    """Cria a instância do App configurada para testes com SQLite em memória."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-key-muito-secreta"
    })

    with app.app_context():
        yield app

@pytest.fixture(scope='function')
def test_db(app):
    """Cria um banco limpo e as tabelas para cada teste."""
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Cliente HTTP para simular requisições."""
    return app.test_client()

@pytest.fixture(scope='function')
def user_mock(test_db):
    """Cria um utilizador de teste na base de dados."""
    user = User(
        spotify_id="tracie_test",
        display_name="Tracie Tester",
        email="tracie@test.com",
        access_token="fake_token",
        refresh_token="fake_refresh"
    )
    test_db.session.add(user)
    test_db.session.commit()
    return user

@pytest.fixture(scope='function')
def auth_client(client, user_mock):
    """
    Cliente que simula um utilizador já autenticado.
    Configura a sessão do Flask com o ID do user_mock.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = str(user_mock.id)
    return client

@pytest.fixture(scope='function', autouse=True)
def mock_spotify():
    """
    O 'Dublê' do Spotify. 
    O 'autouse=True' garante que NENHUM teste tentará ligar-se ao Spotify real.
    """
    with patch('app.services.spotify_service.SpotifyService.get_client') as mocked_get:
        # Criamos um cliente Spotify falso que não faz nada mas aceita chamadas
        fake_sp = MagicMock()
        mocked_get.return_value = fake_sp
        yield mocked_get