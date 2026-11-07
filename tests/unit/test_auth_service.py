from app.models import User
from app.services.auth_service import AuthService


def _token_info():
    return {'access_token': 'novo_token', 'refresh_token': 'novo_refresh', 'expires_at': 1900000000}


def test_login_preenche_account_id_de_usuario_antigo(test_db, user_mock):
    spotify_data = {'id': 'tracie_test', 'account_id': 'acc_123', 'display_name': 'Tracie Tester'}

    user = AuthService._upsert_user(spotify_data, _token_info())

    assert user.id == user_mock.id
    assert user.spotify_account_id == 'acc_123'
    assert test_db.session.query(User).count() == 1


def test_login_acha_usuario_pelo_account_id_mesmo_com_spotify_id_novo(test_db, user_mock):
    user_mock.spotify_account_id = 'acc_123'
    test_db.session.commit()

    spotify_data = {'id': 'tracie_id_novo', 'account_id': 'acc_123', 'display_name': 'Tracie Tester'}

    user = AuthService._upsert_user(spotify_data, _token_info())

    assert user.id == user_mock.id
    assert user.spotify_id == 'tracie_id_novo'
    assert test_db.session.query(User).count() == 1


def test_login_sem_account_id_continua_funcionando(test_db):
    spotify_data = {'id': 'usuario_novo', 'display_name': 'Novo'}

    user = AuthService._upsert_user(spotify_data, _token_info())

    assert user.spotify_id == 'usuario_novo'
    assert user.spotify_account_id is None
