import re
from app.constants import IGNORED_CONTENT_REGEX

def clean_album_title(raw_title: str) -> str:
    """
    Remove sufixos de edição do título do álbum para agrupar as Platinas.
    Ex: "Close to the Edge (Deluxe Edition)" -> "Close to the Edge"
    """
    if not raw_title:
        return ""
        
    title = raw_title
    
    # Busca nas gavetas de edição e ao vivo
    termos = IGNORED_CONTENT_REGEX["EDITIONS"] + IGNORED_CONTENT_REGEX["LIVE"]
    termos_regex = '|'.join(termos)
    
    padrao_parenteses = rf'\s*[\(\[][^\)\]]*\b({termos_regex})\b[^\)\]]*[\)\]]'
    title = re.sub(padrao_parenteses, '', title, flags=re.IGNORECASE)
    
    padrao_hifen = rf'\s*[-—]\s*.*\b({termos_regex})\b.*$'
    title = re.sub(padrao_hifen, '', title, flags=re.IGNORECASE)
    
    return title.strip()

def is_canonical_album(raw_title: str) -> bool:
    """
    Avalia se o álbum é canônico (estúdio). 
    Retorna False para Ao Vivo, Coletâneas ou edições claramente não-canônicas.
    """
    title_lower = raw_title.lower()
    
    # Puxa da gaveta de coletâneas
    for termo in IGNORED_CONTENT_REGEX["COMPILATIONS"]:
        if termo in title_lower:
            return False
            
    # Puxa da gaveta de ao vivo
    for termo in IGNORED_CONTENT_REGEX["LIVE"]:
        if re.search(rf'\b{termo}\b', title_lower):
            return False

    return True

def is_track_skippable(raw_track_name: str) -> bool:
    """
    Avalia se a faixa é um bônus, take alternativo, versão ao vivo 
    ou remix que deve vir com o "X" marcado por padrão.
    """
    track_lower = raw_track_name.lower()
    
    # Acessamos as listas dentro do dicionário importado
    todos_os_termos = (
        IGNORED_CONTENT_REGEX["SKIPPABLE_TRACKS"] + 
        IGNORED_CONTENT_REGEX["LIVE"] + 
        IGNORED_CONTENT_REGEX["EDITIONS"]
    )
    termos_regex = '|'.join(todos_os_termos)
    
    padrao = rf'([\(\[].*\b({termos_regex})\b.*[\)\]]|[-—].*\b({termos_regex})\b)'

    return bool(re.search(padrao, track_lower))