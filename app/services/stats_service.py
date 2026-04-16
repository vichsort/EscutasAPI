from sqlalchemy import func, desc
from app.models import AlbumReview, UserPlatinum, User
from app.extensions import db
from app.services.spotify_service import SpotifyService
from app.services.artist_service import ArtistService
from datetime import date, timedelta
from sqlalchemy import func

class StatsService:

    @staticmethod
    def get_user_stats(user_id: str, request_user_id: str = None) -> dict:
        """
        Calcula as estatísticas pesadas de um usuário direto no banco de dados.
        """
        is_public_view = str(request_user_id) != str(user_id)

        # Total de Reviews
        total_query = db.session.query(AlbumReview).filter(AlbumReview.user_id == user_id)
        if is_public_view:
            total_query = total_query.filter(AlbumReview.is_private == False)
        total_reviews = total_query.count()

        # Total de Platinas (Platinas continuam normais, pois são conquistas de artistas)
        total_plats = db.session.query(UserPlatinum).filter(UserPlatinum.user_id == user_id).count()

        # Overview (A média geral de notas)
        avg_query = db.session.query(func.avg(AlbumReview.score)).filter(AlbumReview.user_id == user_id)
        if is_public_view:
            avg_query = avg_query.filter(AlbumReview.is_private == False)
        
        avg_result = avg_query.scalar() # scalar() pega o valor direto ao invés de uma tupla
        avg_score = round(avg_result, 2) if avg_result else 0.0

        # Distribuição de Tiers (Agrupa e conta)
        tiers_query_base = db.session.query(
            AlbumReview.tier, 
            func.count(AlbumReview.id)
        ).filter(AlbumReview.user_id == user_id)
        
        if is_public_view:
            tiers_query_base = tiers_query_base.filter(AlbumReview.is_private == False)
            
        tiers_query = tiers_query_base.group_by(AlbumReview.tier).all()

        # Inicializa zerado para garantir que o gráfico do front-end não quebre se o cara não tiver tier "F"
        tier_dict = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for tier, count in tiers_query:
            if tier in tier_dict:
                tier_dict[tier] = count

        # Top Artistas Mais Avaliados
        top_artists_base = db.session.query(
            AlbumReview.artist_name, 
            func.count(AlbumReview.id)
        ).filter(AlbumReview.user_id == user_id)
        
        if is_public_view:
            top_artists_base = top_artists_base.filter(AlbumReview.is_private == False)
            
        top_artists_query = top_artists_base\
            .group_by(AlbumReview.artist_name)\
            .order_by(desc(func.count(AlbumReview.id)))\
            .limit(5).all()

        top_artists = [{"name": artist, "count": count} for artist, count in top_artists_query]

        return {
            "overview": {
                "total_reviews": total_reviews,
                "total_platinums": total_plats,
                "average_score": avg_score
            },
            "tier_distribution": tier_dict,
            "top_artists": top_artists
        }

    @staticmethod
    def get_personalized_recommendations(user):
        """
        Pega o artista top 1 do usuário e sugere álbuns que ele ainda não avaliou.
        """
        # Pega os top artistas (pegamos os 3 primeiros pra ter margem)
        top_artists = SpotifyService.get_user_top_artists(user, limit=3)
        
        if not top_artists:
            return []

        recommendations = []
        
        for artist in top_artists:
            # Usa o "Motor de Platina" para ver o que falta
            progress = ArtistService.get_platinum_progress(user, artist['id'])
            
            # Filtra apenas os álbuns que NÃO estão completados
            unheard_albums = [
                album for album in progress['discography'] 
                if not album['is_completed']
            ]
            
            if unheard_albums:
                recommendations.append({
                    "artist_name": artist['name'],
                    "artist_image": artist['images'][0]['url'] if artist['images'] else None,
                    "suggested_albums": unheard_albums[:3] # Sugere até 3 por artista
                })
        
        return recommendations
    
    @staticmethod
    def calculate_and_update_streak(user_id):
        """
        Calcula a streak atual e a maior streak da história do usuário.
        Diferente de um simples contador, ele analisa o calendário de reviews.
        """
        user = User.query.get(user_id)
        if not user:
            return

        # Pega todas as datas únicas em que o usuário fez reviews (ordenadas da mais nova para a mais antiga)
        # Usamos cast para DATE para ignorar as horas
        dates_query = db.session.query(
            func.cast(AlbumReview.created_at, db.Date) 
        ).filter(
            AlbumReview.user_id == user_id
        ).distinct().order_by(desc(func.cast(AlbumReview.created_at, db.Date))).all()

        # Transforma em uma lista de objetos date do Python
        # Ex: [date(2023, 10, 20), date(2023, 10, 19), date(2023, 10, 17)]
        review_dates = [d[0] for d in dates_query]

        if not review_dates:
            user.current_streak = 0
            db.session.commit()
            return

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Verifica se a streak ainda está viva
        # Se a review mais recente não for de hoje nem de ontem, a streak quebrou.
        if review_dates[0] < yesterday:
            user.current_streak = 0
        else:
            # Conta a streak atual
            current_count = 1
            for i in range(len(review_dates) - 1):
                # Se a diferença entre uma data e a próxima for de exatamente 1 dia, a streak continua
                if review_dates[i] - review_dates[i+1] == timedelta(days=1):
                    current_count += 1
                else:
                    # Se houver um buraco de mais de 1 dia, paramos de contar a streak atual
                    break
            user.current_streak = current_count

        # Atualiza a Maior Streak do user (Longest Streak)
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak

        db.session.commit()
        return user.current_streak