import pytest
from app import create_app
from app.extensions import db
from app.models.user import User

@pytest.fixture(scope='module')
def test_app():
    """
    Cria uma instância do App configurada para testes.
    Usa um banco SQLite em memória para ser rápido.
    """
    # Sobrescreve configs para teste
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False
    })

    # Cria o contexto da aplicação
    with app.app_context():
        yield app

@pytest.fixture(scope='function')
def test_db(test_app):
    """
    Cria um banco limpo para CADA teste.
    Depois do teste, apaga tudo.
    """
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()

@pytest.fixture(scope='function')
def user_mock(test_db):
    """
    Cria um usuário fake para usarmos nos testes.
    """
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