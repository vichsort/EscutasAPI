from flask import Blueprint, request
from pydantic import ValidationError

from app.services import InteractionService
from app.utils import require_auth, success_response, paginated_response
from app.schemas import CommentCreate, VoteCreate
from app.exceptions import BusinessRuleError

interactions_bp = Blueprint('interactions', __name__, url_prefix='/api/interactions')

@interactions_bp.route('/comment', methods=['POST'])
@require_auth
def create_comment(current_user):
    """Adiciona um comentário a uma Review ou Post."""
    try:
        data = CommentCreate(**request.json)
    except ValidationError:
        raise BusinessRuleError("Dados inválidos. Verifique se o target_type é 'REVIEW' ou 'POST' e se o content não está vazio.")

    comment = InteractionService.add_comment(
        user_id=current_user.id,
        target_id=str(data.target_id),
        target_type=data.target_type,
        content=data.content
    )
    
    return success_response(
        data=comment.to_dict(), 
        message="Comentário adicionado com sucesso.", 
        status_code=201
    )

@interactions_bp.route('/<string:target_type>/<uuid:target_id>/comments', methods=['GET'])
def get_comments(target_type, target_id):
    """Busca os comentários de algo (paginado)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = InteractionService.get_comments(str(target_id), target_type, page, per_page)
    
    # Converte os objetos do banco para dicionários para o JSON não quebrar
    pagination.items = [item.to_dict() for item in pagination.items]
    
    return paginated_response(pagination, message="Comentários recuperados com sucesso.")

@interactions_bp.route('/comment/<uuid:comment_id>', methods=['DELETE'])
@require_auth
def delete_comment(current_user, comment_id):
    """Deleta um comentário (Apenas o dono pode)."""
    InteractionService.delete_comment(current_user.id, str(comment_id))
    return success_response(message="Comentário deletado com sucesso.")

@interactions_bp.route('/vote', methods=['POST'])
@require_auth
def toggle_vote(current_user):
    """Dá Upvote, Downvote ou Remove o voto existente."""
    try:
        data = VoteCreate(**request.json)
    except ValidationError:
        raise BusinessRuleError("Dados de voto inválidos. Value deve ser 1 ou -1.")

    action = InteractionService.toggle_vote(
        user_id=current_user.id,
        target_id=str(data.target_id),
        target_type=data.target_type,
        value=data.value
    )
    
    counts = InteractionService.get_vote_counts(str(data.target_id), data.target_type)
    
    return success_response(
        data={"action": action, "counts": counts},
        message=f"Voto processado. Ação: {action}."
    )

@interactions_bp.route('/<string:target_type>/<uuid:target_id>/votes', methods=['GET'])
def get_votes(target_type, target_id):
    """Pega o saldo de votos de uma Review, Post ou Comentário."""
    counts = InteractionService.get_vote_counts(str(target_id), target_type)
    return success_response(data=counts, message="Contagem de votos recuperada.")