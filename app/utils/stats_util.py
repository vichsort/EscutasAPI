from sqlalchemy import extract, func
from app.models import AlbumReview

def get_monthly_summary(user_id, month: int, year: int, db_session) -> dict:
    """
    Varre o mês do usuário e devolve um dicionário com estatísticas brutas.
    """
    # Tudo que o usuário fez no mês e ano específicos
    base_query = db_session.query(AlbumReview).filter(
        AlbumReview.user_id == user_id,
        extract('month', AlbumReview.created_at) == month,
        extract('year', AlbumReview.created_at) == year
    )

    # Quantos álbuns ouviu?
    total_reviews = base_query.count()

    # Se o usuário não escreveu nenhuma review no mês, abortamos cedo!
    if total_reviews == 0:
        return None

    # Média Geral
    # O func.avg pede pro próprio PostgreSQL calcular a média, poupando a memória do servidor Python
    avg_rating_query = db_session.query(func.avg(AlbumReview.average_score)).filter(
        AlbumReview.user_id == user_id,
        extract('month', AlbumReview.created_at) == month,
        extract('year', AlbumReview.created_at) == year
    ).scalar()
    
    avg_rating = round(avg_rating_query, 2) if avg_rating_query else 0.0

    # A maior nota do mês
    # Desempate: Se houver dois álbuns com nota 5, pega o mais recente
    best_review = base_query.order_by(
        AlbumReview.average_score.desc(), 
        AlbumReview.created_at.desc()
    ).first()

    # O que vai tocar?
    # Pegamos todos os álbuns que receberam nota maior ou igual a 4.0
    top_reviews = base_query.filter(AlbumReview.average_score >= 4.0).all()
    top_album_ids = [review.spotify_album_id for review in top_reviews]

    return {
        "month": month,
        "year": year,
        "total_reviews": total_reviews,
        "average_rating": avg_rating,
        "best_album_id": best_review.spotify_album_id if best_review else None,
        "best_rating": best_review.average_score if best_review else None, # AQUI
        "top_album_ids": top_album_ids
    }