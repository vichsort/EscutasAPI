import re

TERMOS_EDICAO = [
    'deluxe', 'expanded', 'anniversary', 'bonus', 'special edition', 
    'legacy', 'tour edition', 'remaster', 'mix', 'remix', 'mono', 'stereo'
]

TERMOS_AO_VIVO = [
    'live', 'ao vivo', 'en vivo', 'sessions', 'unplugged', 'concert', 'bbc'
]

TERMOS_COLETANEA = [
    'greatest hits', 'best of', 'anthology', 'essential', 'ultimate', 'platinum collection'
]

TERMOS_FAIXA_IGNORAVEL = [
    'take', 'demo', 'instrumental', 'acappella', 'backing track', 
    'early version', 'alternate', 'alt version', 'rehearsal'
]

def clean_album_title(raw_title: str) -> str:
    """
    Remove sufixos de edição do título do álbum para agrupar as Platinas.
    Ex: "Close to the Edge (Deluxe Edition)" -> "Close to the Edge"
    """
    if not raw_title:
        return ""
        
    title = raw_title
    
    # Monta uma regex dinâmica com os termos de edição e ao vivo
    termos_regex = '|'.join(TERMOS_EDICAO + TERMOS_AO_VIVO)
    
    # Remove tudo entre parênteses/colchetes que contenha nossos termos
    # Ex: (2009 Remaster), [Deluxe Edition]
    padrao_parenteses = rf'\s*[\(\[][^\)\]]*\b({termos_regex})\b[^\)\]]*[\)\]]'
    title = re.sub(padrao_parenteses, '', title, flags=re.IGNORECASE)
    
    # Remove tudo após um hífen/travessão se contiver nossos termos
    # Ex: " - Live at Wembley", " — 2015 Remaster"
    padrao_hifen = rf'\s*[-—]\s*.*\b({termos_regex})\b.*$'
    title = re.sub(padrao_hifen, '', title, flags=re.IGNORECASE)
    
    # Retorna o título limpo, sem espaços extras nas pontas
    return title.strip()

def is_canonical_album(raw_title: str) -> bool:
    """
    Avalia se o álbum é canônico (estúdio). 
    Retorna False para Ao Vivo, Coletâneas ou edições claramente não-canônicas.
    """
    title_lower = raw_title.lower()
    
    # Se o nome INTEIRO for uma coletânea (ex: "Greatest Hits")
    for termo in TERMOS_COLETANEA:
        if termo in title_lower:
            return False
            
    # Se for explicitamente "Ao Vivo" (procura as palavras isoladas)
    # Usamos \b para garantir que 'live' pegue "Live", mas não pegue "Alive" (Pearl Jam) ou "Deliverance"
    for termo in TERMOS_AO_VIVO:
        if re.search(rf'\b{termo}\b', title_lower):
            return False

    return True

def is_track_skippable(raw_track_name: str) -> bool:
    """
    Avalia se a faixa é um bônus/take alternativo que deve vir com o "X" marcado.
    """
    track_lower = raw_track_name.lower()
    
    # Se a faixa tem "take", "demo", "instrumental" nos parênteses ou hífen
    termos_regex = '|'.join(TERMOS_FAIXA_IGNORAVEL)
    
    # Procura especificamente em partes de "detalhe" (entre parênteses ou depois de hífen)
    padrao = rf'([\(\[].*\b({termos_regex})\b.*[\)\]]|[-—].*\b({termos_regex})\b)'
    
    if re.search(padrao, track_lower):
        return True
        
    return False