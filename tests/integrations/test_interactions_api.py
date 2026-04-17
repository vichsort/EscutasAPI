import pytest
from app.models.review import AlbumReview
from app.models.user import User
from app.services.interaction_service import InteractionService
from app.services.curation_service import CurationService

def test_interacoes_comentarios_e_votos(app, test_db, user_mock):
    """
    Simula uma interação social completa:
    1. Usuário A cria uma review.
    2. Usuário B comenta na review.
    3. Usuário B dá um Upvote.
    """
    with app.app_context():
        user_a = test_db.session.get(User, user_mock.id)
        
        user_b = User(spotify_id="senador_b", display_name="Senador B")
        test_db.session.add(user_b)
        test_db.session.commit()

        # O Usuário A posta uma review
        review = AlbumReview(
            user_id=user_a.id,
            spotify_album_id="album_alvo",
            album_name="O Álbum do Ano",
            artist_name="Banda Top",
            review_text="Obra prima inquestionável!"
        )
        test_db.session.add(review)
        test_db.session.commit()

        id_review = str(review.id)
        id_user_b = str(user_b.id)

        # ---------------------------------------------------------
        # COMENTÁRIOS
        # ---------------------------------------------------------
        # O Usuário B tenta adicionar um comentário
        InteractionService.add_comment(
            user_id=id_user_b, 
            target_id=id_review, 
            target_type="review", 
            content="Eu discordo, achei mediano."
        )

        # Vamos buscar os comentários dessa review
        comentarios_paginados = InteractionService.get_comments(target_id=id_review, target_type="review", page=1, per_page=10)
        
        # Acessamos a lista pelo atributo do Pydantic (.items)
        comentarios = comentarios_paginados.items

        assert len(comentarios) == 1
        assert comentarios[0]['content'] == "Eu discordo, achei mediano."
        assert comentarios[0]['author_name'] == "Senador B"

        # ---------------------------------------------------------
        # VOTOS (UPVOTE/DOWNVOTE)
        # ---------------------------------------------------------
        
        # O Usuário B dá um downvote (-1) porque não gostou da review
        InteractionService.toggle_vote(
            user_id=id_user_b,
            target_id=id_review,
            target_type="review",
            value=-1
        )

        # PROVA 1: O downvote foi registrado?
        contagem_negativa = InteractionService.get_vote_counts(target_id=id_review, target_type="review")
        assert contagem_negativa["downvotes"] == 1
        assert contagem_negativa["upvotes"] == 0
        assert contagem_negativa["score"] == -1

        # O Usuário B clica de novo no downvote (Ação de Toggle Off / Retira o voto)
        InteractionService.toggle_vote(
            user_id=id_user_b,
            target_id=id_review,
            target_type="review",
            value=-1
        )

        # PROVA 2: O voto sumiu?
        contagem_zerada = InteractionService.get_vote_counts(target_id=id_review, target_type="review")
        assert contagem_zerada["downvotes"] == 0
        assert contagem_zerada["upvotes"] == 0
        assert contagem_zerada["score"] == 0

        # O Usuário B muda de ideia e dá um Upvote (+1)
        InteractionService.toggle_vote(
            user_id=id_user_b,
            target_id=id_review,
            target_type="review",
            value=1
        )

        # PROVA 3: O Upvote entrou limpo?
        contagem_positiva = InteractionService.get_vote_counts(target_id=id_review, target_type="review")
        assert contagem_positiva["upvotes"] == 1
        assert contagem_positiva["downvotes"] == 0
        assert contagem_positiva["score"] == 1


def test_o_senado_curadoria_da_comunidade(app, test_db, user_mock):
    """
    Testa se o voto da comunidade consegue sobreescrever a Inteligência Artificial/Regex
    na hora de decidir se um álbum é canônico ou não.
    """
    with app.app_context():
        senador = test_db.session.get(User, user_mock.id)

        # O Spotify diz que esse álbum existe e nossa Regex achou suspeito
        id_album_polemico = "spotify_remix_album_123"
        id_album_fantasma = "spotify_album_normal_999"

        # O Senador vota que esse álbum É CANÔNICO (Quebrando a expectativa)
        CurationService.register_vote(
            user_id=senador.id, # O seu método pede user_id, veja se envia str ou o objeto
            spotify_album_id=id_album_polemico,
            is_canonical=True
        )

        # Chamamos o Service para buscar a voz da comunidade para uma lista de IDs
        overrides = CurationService.get_community_overrides([id_album_polemico, id_album_fantasma])

        # VEREDITO: O álbum polêmico DEVE estar no dicionário de overrides como True
        assert id_album_polemico in overrides
        assert overrides[id_album_polemico] is True

        # O álbum fantasma não recebeu votos, logo, não deve ter overrides (vai usar a regex padrão)
        assert id_album_fantasma not in overrides