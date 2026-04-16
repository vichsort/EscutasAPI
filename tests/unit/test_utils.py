from app.utils.title_builder import generate_monthly_title

def test_generate_title_vazio_ou_nulo():
    """Garante que o fallback funciona se o usuário não ouviu gêneros."""
    assert generate_monthly_title([]) == "Mês de Descobertas"
    assert generate_monthly_title(None) == "Mês de Descobertas"

def test_generate_title_lista_simples():
    """Testa se ele identifica corretamente o gênero que mais aparece."""
    genres = ['pop', 'rock', 'rock', 'jazz']
    title = generate_monthly_title(genres)
    
    # Como o nosso utilitário sorteia a frase (ex: "A Fase do Rock", "Mês do Rock"), 
    # nós testamos se a palavra campeã "Rock" está dentro da string final!
    assert "Rock" in title
    assert "Pop" not in title

def test_generate_title_lista_aninhada():
    """Testa se ele lida bem com listas dentro de listas vindas do banco JSON."""
    genres = [['indie rock', 'pop'], 'jazz', ['indie rock']]
    title = generate_monthly_title(genres)
    
    assert "Indie Rock" in title

def test_generate_title_ignora_espacos_e_lixo():
    """Garante que ele limpa espaços em branco e capitaliza as palavras."""
    genres = ['  hip hop  ', 'HIP HOP', 'jazz']
    title = generate_monthly_title(genres)
    
    assert "Hip Hop" in title