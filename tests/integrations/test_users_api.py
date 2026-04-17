import pytest
from flask_jwt_extended import create_access_token
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

def test_parede_de_vidro_reviews_privadas(client, app, test_db, user_mock):
    """
    Garante que o Usuário B não consegue ver a review 'is_private=True' do Usuário A.
    """
    with app.app_context():
        from app.models.user import User
        
        # Pega o Usuário A (Tracie) e cria as reviews dela
        user_a = test_db.session.get(User, user_mock.id)

        # Review Pública (Todo mundo vê)
        r_publica = AlbumReview(
            user_id=user_a.id,
            spotify_album_id="pub_1",
            album_name="Álbum Público",
            artist_name="Banda Aberta",
            is_private=False
        )

        # Review Privada (Ninguém vê, só ela)
        r_privada = AlbumReview(
            user_id=user_a.id,
            spotify_album_id="priv_1",
            album_name="Guilty Pleasure Secreto",
            artist_name="Banda Secreta",
            is_private=True
        )

        # Cria o Usuário B
        user_b = User(
            spotify_id="curioso_b",
            display_name="Invasor Curioso",
        )

        test_db.session.add_all([r_publica, r_privada, user_b])
        test_db.session.commit()

        # Guarda os dados necessários para a requisição antes de fechar o context
        id_user_a = str(user_a.id)
        # crachá do Usuário B
        token_user_b = create_access_token(identity=str(user_b.id))

    # Usuário B tenta listar as reviews do Usuário A
    response = client.get(
        f'/api/users/{id_user_a}/reviews',
        headers={'Authorization': f'Bearer {token_user_b}'}
    )

    # A Parede de Vidro funcionou?
    assert response.status_code == 200
    
    data = response.get_json().get('data', [])
    if isinstance(data, dict) and 'items' in data:
        data = data['items']

    # O Usuário A tem 2 reviews no banco, mas o B só pode receber 1!
    assert len(data) == 1

    # Garante que a review que vazou foi a pública
    assert data[0]['album_name'] == "Álbum Público"

    # Garante que o Segredo absoluto não está em lugar nenhum do JSON
    texto_resposta = str(response.get_json()).lower()
    assert "guilty pleasure secreto" not in texto_resposta