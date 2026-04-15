from sqlalchemy import func, desc
from app.models.review import AlbumReview
from app.models.platinum import UserPlatinum
from app.extensions import db
from app.services.spotify_service import SpotifyService
from app.services.artist_service import ArtistService

class StatsService:
    @staticmethod
    def get_user_stats(user_id: str) -> dict:
        """
        Calcula as estatísticas pesadas de um usuário direto no banco de dados.
        """
        # Overview (A média geral de notas)
        # scalar() pega o valor direto ao invés de uma tupla
        avg_result = db.session.query(func.avg(AlbumReview.score)).filter(AlbumReview.user_id == user_id).scalar()
        avg_score = round(avg_result, 2) if avg_result else 0.0

        total_reviews = db.session.query(AlbumReview).filter(AlbumReview.user_id == user_id).count()
        total_plats = db.session.query(UserPlatinum).filter(UserPlatinum.user_id == user_id).count()

        # Distribuição de Tiers (Agrupa e conta)
        tiers_query = db.session.query(
            AlbumReview.tier, 
            func.count(AlbumReview.id)
        ).filter(AlbumReview.user_id == user_id).group_by(AlbumReview.tier).all()

        # Inicializa zerado para garantir que o gráfico do front-end não quebre se o cara não tiver tier "F"
        tier_dict = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for tier, count in tiers_query:
            if tier in tier_dict:
                tier_dict[tier] = count

        # Top Artistas Mais Avaliados
        top_artists_query = db.session.query(
            AlbumReview.artist_name, 
            func.count(AlbumReview.id)
        ).filter(AlbumReview.user_id == user_id)\
        .group_by(AlbumReview.artist_name)\
        .order_by(desc(func.count(AlbumReview.id)))\
        .limit(5).all() # Pega só o Top 5

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