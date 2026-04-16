import pytest
from datetime import datetime, timedelta, timezone
from app.services.stats_service import StatsService
from app.models.review import AlbumReview
from app.models.user import User

def test_streak_zero_sem_reviews(app, user_mock):
    """Se o usuário não tem nenhuma review no banco, a streak deve ser 0."""
    with app.app_context():
        streak = StatsService.calculate_and_update_streak(str(user_mock.id))
        
        assert streak == 0
        assert user_mock.current_streak == 0

def test_streak_dias_consecutivos(app, test_db, user_mock):
    """Testa se a streak soma 2 se ele tem review hoje e ontem."""
    with app.app_context():
        hoje = datetime.now(timezone.utc)
        ontem = hoje - timedelta(days=1)

        r1 = AlbumReview(user_id=user_mock.id, spotify_album_id="id1", album_name="A", artist_name="A", created_at=hoje)
        r2 = AlbumReview(user_id=user_mock.id, spotify_album_id="id2", album_name="B", artist_name="B", created_at=ontem)
        
        test_db.session.add_all([r1, r2])
        test_db.session.commit()

        streak = StatsService.calculate_and_update_streak(str(user_mock.id))
        
        updated_user = test_db.session.get(User, user_mock.id)
        
        assert streak == 2
        assert updated_user.current_streak == 2
        assert updated_user.longest_streak == 2

def test_streak_quebrada_por_esquecimento(app, test_db, user_mock):
    """Se a última review foi há mais de 1 dia atrás, a streak deve ser cortada (0)."""
    with app.app_context():
        anteontem = datetime.now(timezone.utc) - timedelta(days=2)

        # Busca o usuário vivo no banco de dados para poder alterar os status dele
        fresh_user = test_db.session.get(User, user_mock.id)
        fresh_user.longest_streak = 5
        
        # Cria a review falsa e salva tudo
        r1 = AlbumReview(user_id=fresh_user.id, spotify_album_id="id1", album_name="A", artist_name="A", created_at=anteontem)
        test_db.session.add(r1)
        test_db.session.commit()

        # Roda o nosso serviço de gamificação
        streak = StatsService.calculate_and_update_streak(str(fresh_user.id))
        
        # Busca os resultados finais atualizados
        updated_user = test_db.session.get(User, fresh_user.id)
        
        assert streak == 0
        assert updated_user.current_streak == 0
        assert updated_user.longest_streak == 5