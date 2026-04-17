from sqlalchemy import func
from app.extensions import db
from app.schemas import PaginatedCommentResponse
from app.models import Comment, Vote, AlbumReview,BlogPost
from app.exceptions import BusinessRuleError, ResourceNotFoundError

class InteractionService:

    @staticmethod
    def _validate_target(target_id: str, target_type: str):
        """
        Método interno guardião para garantir que o alvo do comentário/voto realmente existe.
        """
        target_type = target_type.upper()
        if target_type == 'REVIEW':
            target = db.session.get(AlbumReview, target_id)
        elif target_type == 'POST':
            target = db.session.get(BlogPost, target_id)
        elif target_type == 'COMMENT':
            target = db.session.get(Comment, target_id)
        else:
            raise BusinessRuleError("Tipo de alvo inválido. Use 'REVIEW', 'POST' ou 'COMMENT'.")

        if not target:
            raise ResourceNotFoundError(f"O alvo ({target_type}) não foi encontrado.")
        
        return target_type

    @staticmethod
    def add_comment(user_id: str, target_id: str, target_type: str, content: str):
        """Cria um novo comentário."""
        if not content or not str(content).strip():
            raise BusinessRuleError("O comentário não pode estar vazio.")

        valid_type = InteractionService._validate_target(target_id, target_type)
        
        # Não permitimos comentários em comentários nesta versão para evitar complexidade extra.
        if valid_type == 'COMMENT':
            raise BusinessRuleError("Não é possível responder a um comentário diretamente nesta versão.")

        new_comment = Comment(
            user_id=user_id,
            target_id=target_id,
            target_type=valid_type,
            content=content.strip()
        )
        db.session.add(new_comment)
        db.session.commit()
        return new_comment

    @staticmethod
    def get_comments(target_id: str, target_type: str, page: int = 1, per_page: int = 10):
        """Busca os comentários de forma paginada."""
        valid_type = target_type.upper()
        
        paginacao = db.session.query(Comment).filter_by(
            target_id=target_id, 
            target_type=valid_type
        ).order_by(Comment.created_at.desc()).paginate(page=page, per_page=per_page)

        return PaginatedCommentResponse(
            items=[c.to_dict() for c in paginacao.items],
            total=paginacao.total,
            page=paginacao.page,
            pages=paginacao.pages
        )

    @staticmethod
    def delete_comment(user_id: str, comment_id: str):
        """Deleta um comentário (Apenas o autor pode deletar)."""
        comment = Comment.query.filter_by(id=comment_id, user_id=user_id).first()
        if not comment:
            raise ResourceNotFoundError("Comentário não encontrado ou você não tem permissão para apagá-lo.")
        
        db.session.delete(comment)
        db.session.commit()
        return True

    @staticmethod
    def toggle_vote(user_id: str, target_id: str, target_type: str, value: int):
        """
        Lógica inteligente de Toggle:
        - Clicou Upvote e não tinha voto? Cria +1.
        - Clicou Upvote e já tinha Upvote? Remove o voto (fica 0).
        - Clicou Upvote e tinha Downvote? Atualiza para +1.
        """
        if value not in [1, -1]:
            raise BusinessRuleError("O voto deve ser 1 (Upvote) ou -1 (Downvote).")

        valid_type = InteractionService._validate_target(target_id, target_type)
        
        vote = Vote.query.filter_by(
            user_id=user_id, 
            target_id=target_id, 
            target_type=valid_type
        ).first()

        action_result = "added"

        if vote:
            if vote.value == value:
                # Clicou no mesmo botão que já estava ativo: Remove o voto
                db.session.delete(vote)
                action_result = "removed"
            else:
                # Trocou de ideia (ex: era Downvote, virou Upvote)
                vote.value = value
                action_result = "updated"
        else:
            # Não existia voto, cria um novo
            new_vote = Vote(
                user_id=user_id,
                target_id=target_id,
                target_type=valid_type,
                value=value
            )
            db.session.add(new_vote)

        db.session.commit()
        return action_result

    @staticmethod
    def get_vote_counts(target_id: str, target_type: str):
        """
        Calcula rapidamente o total de Upvotes, Downvotes e o Saldo (Score).
        """
        valid_type = target_type.upper()
        
        # Usamos o banco para somar tudo de uma vez
        votes = db.session.query(
            Vote.value, 
            func.count(Vote.id)
        ).filter_by(
            target_id=target_id, 
            target_type=valid_type
        ).group_by(Vote.value).all()

        upvotes = 0
        downvotes = 0

        for val, count in votes:
            if val == 1:
                upvotes = count
            elif val == -1:
                downvotes = count

        return {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "score": upvotes - downvotes
        }