from sqlalchemy import extract, func, desc
from app.models import AlbumReview, UserPlatinum
from app.extensions import db

#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# FUNÇÕES PARA O STATS SERVICE - - - - - - - - - - - - - - - - - - - - - - - - 
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# obs. tudo aqui pra baixo em tese seria um repository, mas no momento só esse
# endpoiint de estatísticas é que precisa dessas queries mais complexas, então 
# deixei aqui por enquanto. Se a gente precisar dessas queries em outros lugares, 
# aí sim a gente refatora pra conter os tais repositories - gostaria de fazer
# agora já, mas vai aumentar a complexidade desnecessariamente.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# get_user_stats - - - - - - - - - - - - - - - - - - - - - - - - 
def count_user_reviews(user_id: str, is_public_view: bool, db_session) -> int:
    """Conta o total de reviews do usuário, respeitando a privacidade."""
    query = db_session.query(AlbumReview).filter(AlbumReview.user_id == user_id)
    if is_public_view:
        query = query.filter(AlbumReview.is_private == False)
    return query.count()

def count_user_platinums(user_id: str, db_session) -> int:
    """Conta o total de platinas de um usuário."""
    return db_session.query(UserPlatinum).filter(UserPlatinum.user_id == user_id).count()

def calculate_average_score(user_id: str, is_public_view: bool, db_session) -> float:
    """Calcula a média geral das notas do usuário."""
    query = db_session.query(func.avg(AlbumReview.average_score)).filter(AlbumReview.user_id == user_id)
    if is_public_view:
        query = query.filter(AlbumReview.is_private == False)
    
    result = query.scalar()
    return round(result, 2) if result else 0.0

def get_tier_distribution(user_id: str, is_public_view: bool, db_session) -> dict:
    """Calcula a distribuição de Tiers (S, A, B, C, D, F) para os gráficos."""
    query = db_session.query(
        AlbumReview.tier, 
        func.count(AlbumReview.id)
    ).filter(AlbumReview.user_id == user_id)
    
    if is_public_view:
        query = query.filter(AlbumReview.is_private == False)
        
    results = query.group_by(AlbumReview.tier).all()
    
    tier_dict = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for tier, count in results:
        if tier in tier_dict:
            tier_dict[tier] = count
    return tier_dict

def get_top_artists(user_id: str, is_public_view: bool, db_session, limit: int = 5) -> list:
    """Retorna os artistas mais avaliados pelo usuário."""
    query = db_session.query(
        AlbumReview.artist_name, 
        func.count(AlbumReview.id)
    ).filter(AlbumReview.user_id == user_id)
    
    if is_public_view:
        query = query.filter(AlbumReview.is_private == False)
        
    results = query.group_by(AlbumReview.artist_name)\
                    .order_by(desc(func.count(AlbumReview.id)))\
                    .limit(limit).all()
                    
    return [{"name": artist, "count": count} for artist, count in results]

# get_personalized_recommendations - - - - - - - - - - - - - - - - -
def get_community_bubble(user_id: str, db_session, limit: int = 5):
    """
    Retorna os álbuns mais aclamados pela comunidade (Tier S) 
    que o usuário ainda NÃO avaliou.
    """
    # Subquery: IDs dos álbuns que o utilizador JÁ avaliou
    reviewed_ids = db_session.query(AlbumReview.spotify_album_id).filter(
        AlbumReview.user_id == user_id
    ).subquery()

    # Busca álbuns Tier S na comunidade que não estão na subquery
    bubble_query = db_session.query(
        AlbumReview.spotify_album_id,
        AlbumReview.album_name,
        AlbumReview.artist_name,
        AlbumReview.cover_url,
        func.count(AlbumReview.id).label('total_votes')
    ).filter(
        AlbumReview.tier == 'S',
        AlbumReview.is_private == False,
        AlbumReview.spotify_album_id.not_in(reviewed_ids)
    ).group_by(
        AlbumReview.spotify_album_id, 
        AlbumReview.album_name, 
        AlbumReview.artist_name, 
        AlbumReview.cover_url
    ).order_by(desc('total_votes')).limit(limit).all()

    return bubble_query

# calculate_and_update_streak - - - - - - - - - - - - - - - -
def get_user_review_dates(user_id: str, db_session) -> list:
    """
    Busca todas as datas únicas (ignorando horas) em que o usuário 
    fez reviews, ordenadas da mais recente para a mais antiga.
    """
    dates_query = db_session.query(
        func.cast(AlbumReview.created_at, db.Date) 
    ).filter(
        AlbumReview.user_id == user_id
    ).distinct().order_by(desc(func.cast(AlbumReview.created_at, db.Date))).all()

    # Retorna uma lista limpa de objetos date do Python
    # Ex: [date(2023, 10, 20), date(2023, 10, 19)]
    return [d[0] for d in dates_query]

#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# FIM DAS FUNÇÕES PARA O STATS SERVICE - - - - - - - - - - - - - - - - - - - -
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

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