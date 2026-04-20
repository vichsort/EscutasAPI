import pytest
from app.models import BlogPost, BlogPostMention

def test_ciclo_de_vida_do_blog_com_mencoes(auth_client, test_db):
    """
    Testa o fluxo completo: Criar -> Ler -> Atualizar -> Deletar.
    Garante que as menções polimórficas estão sendo sincronizadas perfeitamente.
    """
    # ---------------------------------------------------------
    # CRIAÇÃO (POST)
    # ---------------------------------------------------------
    payload_criacao = {
        "title": "A Evolução do Daft Punk",
        "content": "Eles mudaram a música eletrônica para sempre...",
        "summary": "Um review sobre a carreira da dupla.",
        "mentions": [
            {"target_type": "ARTIST", "target_id": "daft_punk_id", "target_name": "Daft Punk"},
            {"target_type": "ALBUM", "target_id": "discovery_id", "target_name": "Discovery"}
        ]
    }

    response_create = auth_client.post('/api/blog', json=payload_criacao)
    print(response_create)
    data_create = response_create.get_json()['data']


    assert response_create.status_code == 201
    assert data_create['title'] == "A Evolução do Daft Punk"
    assert data_create['slug'] == "a-evolu-o-do-daft-punk" 
    assert len(data_create['mentions']) == 2
    
    post_id = data_create['id']
    post_slug = data_create['slug']

    # ---------------------------------------------------------
    # ATUALIZAÇÃO E SYNC DE MENÇÕES (PUT)
    # ---------------------------------------------------------
    payload_atualizacao = {
        "status": "PUBLISHED", 
        "title": "A Magia do Daft Punk",
        "mentions": [
            # Mantemos o artista
            {"target_type": "ARTIST", "target_id": "daft_punk_id", "target_name": "Daft Punk"},
            # REMOVEMOS o álbum Discovery e ADICIONAMOS a música One More Time
            {"target_type": "TRACK", "target_id": "one_more_time_id", "target_name": "One More Time"}
        ]
    }

    response_update = auth_client.put(f'/api/blog/{post_id}', json=payload_atualizacao)
    data_update = response_update.get_json()['data']

    assert response_update.status_code == 200
    assert data_update['status'] == "PUBLISHED"
    assert data_update['title'] == "A Magia do Daft Punk"
    assert len(data_update['mentions']) == 2
    tipos_de_mencoes = [m['target_type'] for m in data_update['mentions']]
    assert "ARTIST" in tipos_de_mencoes
    assert "TRACK" in tipos_de_mencoes
    assert "ALBUM" not in tipos_de_mencoes # O Discovery tem que ter sumido!

    # ---------------------------------------------------------
    # LEITURA PÚBLICA (GET)
    # ---------------------------------------------------------
    # Agora que está PUBLISHED, a leitura pública deve funcionar
    response_get = auth_client.get(f'/api/blog/{post_slug}')
    assert response_get.status_code == 200

    # ---------------------------------------------------------
    # EXCLUSÃO EM CASCATA (DELETE)
    # ---------------------------------------------------------
    response_delete = auth_client.delete(f'/api/blog/{post_id}')
    assert response_delete.status_code == 200

    # Verifica se sumiu mesmo
    response_get_after = auth_client.get(f'/api/blog/{post_slug}')
    assert response_get_after.status_code == 404

    # Vai direto no banco e garante que a tabela de menções limpou (Cascade Delete)
    mencoes_sobrando = test_db.session.query(BlogPostMention).filter_by(post_id=post_id).count()
    assert mencoes_sobrando == 0 


def test_gerador_inteligente_de_slugs(auth_client):
    """
    Garante que se dois posts tiverem o mesmo título, o sistema
    não quebra e adiciona os sufixos numéricos corretamente.
    """
    payload = {
        "title": "Os Melhores de 2025",
        "content": "Texto genérico",
        "mentions": []
    }

    # Post 1 (Original)
    r1 = auth_client.post('/api/blog', json=payload)
    assert r1.get_json()['data']['slug'] == "os-melhores-de-2025"

    # Post 2 (Clonado, o utils deve botar -1)
    r2 = auth_client.post('/api/blog', json=payload)
    assert r2.get_json()['data']['slug'] == "os-melhores-de-2025-1"

    # Post 3 (Mais um clone, o utils deve botar -2)
    r3 = auth_client.post('/api/blog', json=payload)
    assert r3.get_json()['data']['slug'] == "os-melhores-de-2025-2"