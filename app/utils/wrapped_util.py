from app.constants import WRAPPED_MONTHLY_TEMPLATE, MESES

def generate_monthly_post_content(
    month: int, 
    year: int, 
    stats: dict, 
    best_album_name: str, 
    best_album_artist: str, 
    playlist_url: str
) -> tuple[str, str, str]:
    """
    Retorna uma tupla contendo: (Título, Resumo, Conteúdo em Markdown)
    """
    nome_mes = MESES.get(month, "Mês")
    
    # Título e Resumo simples
    title = f"Meu Resumo Musical: {nome_mes} de {year} 🎧"
    summary = f"Uma viagem por {stats['total_reviews']} álbuns. Descubra qual foi o meu favorito e ouça a playlist com os melhores do mês!"

    # O Preenchimento do Template
    content = WRAPPED_MONTHLY_TEMPLATE.format(
        nome_mes=nome_mes,
        total_reviews=stats['total_reviews'],
        average_rating=stats['average_rating'],
        best_album_name=best_album_name,
        best_album_artist=best_album_artist,
        best_rating=stats['best_rating'],
        playlist_url=playlist_url
    )

    return title, summary, content.strip()