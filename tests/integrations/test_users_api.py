import pytest
from datetime import datetime, timezone
from app.models.review import AlbumReview

def test_get_user_stats_para_badges(auth_client, app, test_db, user_mock):
    """
    Garante que a rota de stats devolve as métricas necessárias 
    para o Front-end gerar as Badges (Streaks, Totais, Tier Distribution).
    """
    hoje = datetime.now(timezone.utc)

    # Preparando o terreno: Inserindo uma review Tier S no banco
    with app.app_context():
        # 'refresh' manual
        from app.models.user import User
        fresh_user = test_db.session.get(User, user_mock.id)
        
        # Vamos simular que ele está "On Fire" com uma streak de 7 dias
        fresh_user.current_streak = 7 
        fresh_user.longest_streak = 15

        r1 = AlbumReview(
            user_id=fresh_user.id, 
            spotify_album_id="badge_album", 
            album_name="Badge Maker", 
            artist_name="The Testers", 
            average_score=10.0,
            tier="S",
            created_at=hoje
        )
        test_db.session.add(r1)
        test_db.session.commit()

    # Chamamos a rota usando o nosso cliente VIP (que passa pelo @require_auth)
    # Como definimos <string:user_param>, usar 'me' deve resolver magicamente para o user logado!
    response = auth_client.get('/api/users/me/stats')
    
    # O Front-end tem tudo o que precisa?
    assert response.status_code == 200
    
    data = response.get_json()['data']
    
    assert 'current_streak' in data['overview']
    assert isinstance(data['overview']['current_streak'], int)
    
    assert 'longest_streak' in data['overview']
    assert isinstance(data['overview']['longest_streak'], int)
    
    # Garante que as outras métricas da overview estão lá
    assert 'total_reviews' in data['overview']
    assert data['overview']['average_score'] == 10.0
    
    # Verifica a distribuição para desenhar a Tierlist
    assert data['tier_distribution']['S'] == 1
    assert data['tier_distribution']['A'] == 0