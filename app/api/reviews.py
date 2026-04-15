from flask import Blueprint, request
from app.utils import success_response, require_auth
from app.services import ReviewService
from app.extensions import limiter
from app.models import AlbumReview
from app.schemas import ReviewFull, ReviewCreate
from app.exceptions import ResourceNotFoundError

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')

@reviews_bp.route('', methods=['POST'])
@require_auth
@limiter.limit("5 per minute")
def create_review(current_user):
    """
    Cria uma nova review completa.
    """
    payload_validado = ReviewCreate.model_validate(request.json)

    result_orm = ReviewService.create_review(current_user, payload_validado.model_dump())

    return success_response(
        data=ReviewFull.model_validate(result_orm).model_dump(),
        message="Review salva com sucesso!",
        status_code=201
    )

@reviews_bp.route('/<uuid:review_id>', methods=['GET'])
def get_review_details(review_id):
    """
    Busca review pelo UUID.
    """
    review = AlbumReview.query.get(review_id)
    if not review:
        raise ResourceNotFoundError("Review")
    
    return success_response(
        data=ReviewFull.model_validate(review).model_dump()
    )