from flask import Blueprint, request
from app.services.blog_service import BlogService
from app.schemas.blog import PostCreate, PostUpdate, BlogPostDetail, BlogPostList
from app.utils.decorator_util import require_auth
from app.utils.response_util import success_response, paginated_response

blog_bp = Blueprint('blog', __name__, url_prefix='/api/blog')

# --- ROTAS PÚBLICAS (Leitura) ---

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

    return success_response(
        data=BlogPostDetail.model_validate(post).model_dump()
    )

@blog_bp.route('', methods=['POST'])
@require_auth
def create_post(current_user):
    """
    Cria um novo post (Draft).
    O Service vai ler o conteúdo e gerar o Snapshot das músicas automaticamente.
    """
    payload = PostCreate(**request.json)
    new_post = BlogService.create_post(current_user, payload.model_dump())
    
    return success_response(
        data=BlogPostDetail.model_validate(new_post).model_dump(),
        message="Rascunho criado com sucesso!",
        status_code=201
    )

@blog_bp.route('/<post_id>', methods=['PUT'])
@require_auth
def update_post(current_user, post_id):
    """
    Atualiza um post.
    Se o texto mudou, o Service regenera os metadados das músicas.
    """
    payload = PostUpdate(**request.json)
    
    updated_post = BlogService.update_post(
        post_id, 
        current_user.id, 
        payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        data=BlogPostDetail.model_validate(updated_post).model_dump(),
        message="Post atualizado com sucesso!"
    )