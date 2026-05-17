from app.models import User, AlbumReview
from app.extensions import db
from app.utils import count_user_reviews, count_user_platinums, calculate_average_score, get_tier_distribution, get_top_artists, get_user_review_dates
from app.services.spotify_service import SpotifyService
from app.services.artist_service import ArtistService
from datetime import date, timedelta

class StatsService:

    @staticmethod
    def get_user_stats(user_id: str, request_user_id: str = None) -> dict:
        """
        Calcula as estatísticas de um usuário, delegando as queries pesadas 
        para o utilitário de banco de dados (StatsUtil).
        """
        is_public_view = str(request_user_id) != str(user_id)

        total_reviews = count_user_reviews(user_id, is_public_view, db.session)
        total_plats = count_user_platinums(user_id, db.session)
        avg_score = calculate_average_score(user_id, is_public_view, db.session)
        tier_dict = get_tier_distribution(user_id, is_public_view, db.session)
        top_artists = get_top_artists(user_id, is_public_view, db.session)

        total_artists = db.session.query(
            db.func.count(db.func.distinct(AlbumReview.artist_name))
        ).filter(AlbumReview.user_id == user_id)

        if is_public_view:
            total_artists = total_artists.filter(AlbumReview.is_private == False)

        total_artists_reviewed = total_artists.scalar() or 0

        user = db.session.get(User, user_id)

        return {
            "overview": {
                "total_reviews": total_reviews,
                "total_platinums": total_plats,
                "total_artists_reviewed": total_artists_reviewed,
                "average_score": avg_score,
                "current_streak": user.current_streak if user else 0,
                "longest_streak": user.longest_streak if user else 0
            },
            "tier_distribution": tier_dict,
            "top_artists": top_artists
        }

    @staticmethod
    def get_platinum_focus(user) -> list:
        """
        Sugere álbuns que faltam para platinar nos artistas favoritos do usuário.
        """
        result = []

        top_artists = SpotifyService.get_user_top_artists(user, limit=3)
        for artist in top_artists:
            progress = ArtistService.get_platinum_progress(user, artist['id'])
            unheard = [a for a in progress['discography'] if not a['is_completed']]
            if unheard:
                result.append({
                    "artist_name": artist['name'],
                    "suggested_albums": unheard[:2]
                })

        return result
    
    @staticmethod
    def calculate_and_update_streak(user_id):
        """
        Calcula a streak atual e a maior streak da história do usuário.
        Diferente de um simples contador, ele analisa o calendário de reviews.
        """
        user = db.session.get(User, user_id)
        if not user:
            return 0

        # busca datas
        review_dates = get_user_review_dates(user_id, db.session)

        # se não tem datas, zera a streak
        if not review_dates:
            user.current_streak = 0
            db.session.commit()
            return 0

        today = date.today()
        yesterday = today - timedelta(days=1)

        # verifica se a streak ainda está viva
        if review_dates[0] < yesterday:
            user.current_streak = 0
        else:
            # Conta a streak atual
            current_count = 1
            for i in range(len(review_dates) - 1):
                # Se a diferença for exatamente 1 dia, a streak continua
                if review_dates[i] - review_dates[i+1] == timedelta(days=1):
                    current_count += 1
                else:
                    # Se houver um buraco, quebrou a streak atual
                    break
            user.current_streak = current_count

        # Atualiza a Maior Streak do user (Longest Streak)
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak

        db.session.commit()
        return user.current_streak