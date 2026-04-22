import pytest
import time
from app.extensions import cache

def test_cache_leitura_e_escrita_basica(app):
    """
    Testa se o cache consegue guardar uma informação simples 
    e recuperar logo em seguida.
    """
    with app.app_context():
        cache.clear()

        # Salvamos um valor qualquer com uma chave específica
        cache.set('teste_chave', 'valor_secreto', timeout=10)

        # Tentamos recuperar
        resultado = cache.get('teste_chave')

        assert resultado == 'valor_secreto'


def test_cache_memoize_evita_reprocessamento(app):
    """
    Testa o decorador @cache.memoize (o mesmo que usamos no SearchService).
    Prova que se a gente chamar a mesma função duas vezes com os mesmos
    parâmetros, ela só executa de verdade na primeira vez.
    """
    with app.app_context():
        cache.clear()

        # Dicionário de controle para sabermos quantas vezes a função rodou de verdade
        controle = {'execucoes': 0}

        # Criamos uma função simulando algo pesado
        @cache.memoize(timeout=50)
        def funcao_pesada_simulada(parametro):
            controle['execucoes'] += 1
            return f"processado_{parametro}"

        # 1ª Chamada (Vai executar a função e salvar no cache)
        resultado_1 = funcao_pesada_simulada("A")
        assert resultado_1 == "processado_A"
        assert controle['execucoes'] == 1

        # 2ª Chamada com o MESMO parâmetro (NÃO deve executar a função, pega do cache)
        resultado_2 = funcao_pesada_simulada("A")
        assert resultado_2 == "processado_A"
        assert controle['execucoes'] == 1  # O número de execuções continua 1! Mágica do cache.

        # 3ª Chamada com um parâmetro DIFERENTE (Deve executar a função de novo)
        resultado_3 = funcao_pesada_simulada("B")
        assert resultado_3 == "processado_B"
        assert controle['execucoes'] == 2  # Agora sim subiu para 2!