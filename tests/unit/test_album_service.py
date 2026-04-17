import pytest
from app.utils import is_track_skippable, clean_album_title, is_canonical_album

# O 'parametrize' vai rodar o teste abaixo VÁRIAS vezes, 
# uma para cada tupla desta lista (nome_da_faixa, resultado_esperado)
@pytest.mark.parametrize("track_name, expected_ignore", [
    # --- FAIXAS NORMAIS (Obrigatórias, devem retornar False) ---
    ("Tribunal de Rua", False),
    ("Me Deixa", False),
    
    # --- A INTELIGÊNCIA DA REGEX (A palavra existe, mas é o nome da música -> False) ---
    ("Take On Me", False), 
    ("Instrumental de Abertura", False),
    ("Live and Let Die", False), # "Live" está no título principal, não é versão!
    
    # --- FAIXAS IGNORÁVEIS (Takes, Demos, Instrumentais -> True) ---
    ("Can't Stop (Demo)", True),
    ("Me Deixa - Instrumental", True),
    ("Tribunal de Rua (Take 2)", True),
    
    # --- AO VIVO E EDIÇÕES (O mundo real -> True) ---
    ("Can't Stop (Live at Wembley)", True),
    ("Tribunal de Rua - Remix", True),
    ("Epitáfio [2001 Remaster]", True),
    ("Me Deixa - Bonus Track", True)
])

def test_inteligencia_regex_faixas_ignoradas(track_name, expected_ignore):
    """
    Testa se o sistema sugere corretamente ignorar faixas bônus, alternativas,
    ao vivo e remixes, respeitando os parênteses e hífens.
    """
    resultado = is_track_skippable(track_name)
    
    assert resultado == expected_ignore, f"A Regex falhou para a faixa: '{track_name}'. Esperava {expected_ignore}."

@pytest.mark.parametrize("raw_title, expected_clean_title", [
    ("Close to the Edge", "Close to the Edge"),
    ("Close to the Edge (Deluxe Edition)", "Close to the Edge"),
    ("The Black Parade [2006 Remaster]", "The Black Parade"),
    ("Rumours - Live", "Rumours"),
    ("MTV Unplugged in New York", "MTV Unplugged in New York"), # Não mexe se for o nome principal!
    ("A Night at the Opera (30th Anniversary Mix) - Bonus Track Version", "A Night at the Opera")
])

def test_limpeza_de_titulo_de_album(raw_title, expected_clean_title):
    """Garante que a Regex limpa os sufixos de álbuns perfeitamente."""
    assert clean_album_title(raw_title) == expected_clean_title

@pytest.mark.parametrize("album_title, is_canonical", [
    ("The Dark Side of the Moon", True),
    ("Alive 2007", True),
    ("Greatest Hits", False),
    ("The Best Of Queen", False),
    ("Live at River Plate", False),
    ("MTV Unplugged in New York", False)
])
def test_album_canonico(album_title, is_canonical):
    """Garante que coletâneas e discos ao vivo são barrados da Platina."""
    assert is_canonical_album(album_title) == is_canonical