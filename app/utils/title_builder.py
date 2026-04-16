import random
from collections import Counter
from typing import List, Union
from app.constants import MONTH_TITLE_PRESETS


def generate_monthly_title(genres: List[Union[str, List[str]]]) -> str:
    """
    Recebe uma lista bruta de gêneros puxada do banco de dados 
    e devolve um título criativo baseado no gênero mais ouvido.
    """
    if not genres:
        return "Mês de Descobertas"  # Fallback elegante caso ele não tenha ouvido nada com gênero

    cleaned_genres = []
    
    for item in genres:
        # Como o banco pode guardar como lista de strings (JSON/Array), precisamos tratar
        if isinstance(item, list):
            cleaned_genres.extend([g.strip().title() for g in item if g])
        elif isinstance(item, str):
            cleaned_genres.append(item.strip().title())

    if not cleaned_genres:
        return "Mês de Descobertas"

    # Conta quem apareceu mais! 
    # Ex: [('Rock', 15), ('Pop', 8), ('Jazz', 2)]
    counter = Counter(cleaned_genres)
    
    # Pega a tupla do campeão (ex: 'Rock')
    top_genre, _ = counter.most_common(1)[0]

    # Sorteia uma frase e injeta o gênero campeão
    template = random.choice(MONTH_TITLE_PRESETS)
    return template.format(genre=top_genre)