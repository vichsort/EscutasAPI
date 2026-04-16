from flask import Blueprint, request
from app.services import BlogService
from app.schemas import PostCreate, PostUpdate, BlogPostDetail, BlogPostList
from app.utils import success_response, paginated_response, require_auth
from app.exceptions import ResourceNotFoundError

blog_bp = Blueprint('blog', __name__, url_prefix='/api/blog')

@blog_bp.route('', methods=['GET'])
def list_posts():
    """
    Lista os posts publicados.
    Público: Qualquer um pode ver.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = BlogService.list_posts(page, per_page, public_only=True)
    data = [BlogPostList.model_validate(post).model_dump() for post in pagination.items]
    pagination.items = data
    
    return paginated_response(pagination)

@blog_bp.route('/<slug>', methods=['GET'])
def get_post(slug):
    """
    Lê um post específico pelo Slug (URL amigável).
    Ex: GET /api/blog/o-album-do-ano
    """
    post = BlogService.get_post_by_slug(slug, public_only=True)

    if not post:
        raise ResourceNotFoundError("Post")

    return success_response(
        data=BlogPostDetail.model_validate(post).model_dump()
    )

@blog_bp.route('', methods=['POST'])
@require_auth
def create_post(current_user):
    """
    Cria um novo post (Draft).
    """
    payload = PostCreate.model_validate(request.json)
    
    new_post = BlogService.create_post(current_user, payload.model_dump())
    
    return success_response(
        data=BlogPostDetail.model_validate(new_post).model_dump(),
        message="Rascunho criado com sucesso!",
        status_code=201
    )

@blog_bp.route('/<uuid:post_id>', methods=['PUT'])
@require_auth
def update_post(current_user, post_id):
    """
    Atualiza um post.
    """
    payload = PostUpdate.model_validate(request.json)
    
    updated_post = BlogService.update_post(
        post_id=post_id, 
        user_id=current_user.id,
        update_data=payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        data=BlogPostDetail.model_validate(updated_post).model_dump(),
        message="Post atualizado com sucesso!"
    )

@blog_bp.route('/<uuid:post_id>', methods=['DELETE'])
@require_auth
def delete_post(current_user, post_id):
    """
    Deleta um post do blog. Apenas o próprio autor consegue realizar esta ação.
    """
    BlogService.delete_post(post_id=str(post_id), user_id=current_user.id)
    
    return success_response(
        message="Post deletado com sucesso."
    )