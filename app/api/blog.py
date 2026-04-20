from flask import Blueprint, request
from app.services import BlogService
from app.schemas import PostCreate, PostUpdate
from app.utils import success_response, require_auth

blog_bp = Blueprint('blog', __name__, url_prefix='/api/blog')

@blog_bp.route('', methods=['GET'])
def list_posts():
    """
    Lista os posts publicados.
    Público: Qualquer um pode ver.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # O Service já devolve o PaginatedBlogPostResponse (Pydantic)
    paginated_data = BlogService.list_posts(page, per_page, public_only=True)
    
    return success_response(
        data=paginated_data.model_dump(mode='json'),
        message="Posts listados com sucesso."
    )

@blog_bp.route('/<slug>', methods=['GET'])
def get_post(slug):
    """
    Lê um post específico pelo Slug (URL amigável).
    Ex: GET /api/blog/o-album-do-ano
    """
    # O Service já lança o erro 404 se não achar, e já devolve o BlogPostDetail (Pydantic)
    post = BlogService.get_post_by_slug(slug, public_only=True)

    return success_response(
        data=post.model_dump(mode='json'),
        message="Post recuperado com sucesso."
    )

@blog_bp.route('', methods=['POST'])
@require_auth
def create_post(current_user):
    """
    Cria um novo post (Draft).
    Espera receber o conteúdo e as menções polimórficas (mentions).
    """
    # Valida a entrada da requisição
    payload = PostCreate.model_validate(request.json)
    
    # Passa o DTO inteiro pro Service trabalhar
    new_post = BlogService.create_post(current_user, payload)
    
    return success_response(
        data=new_post.model_dump(mode='json'),
        message="Rascunho criado com sucesso!",
        status_code=201
    )

@blog_bp.route('/<uuid:post_id>', methods=['PUT'])
@require_auth
def update_post(current_user, post_id):
    """
    Atualiza um post e sincroniza as menções polimórficas.
    """
    # Valida a entrada da requisição
    payload = PostUpdate.model_validate(request.json)
    
    # Passa o DTO inteiro pro Service
    updated_post = BlogService.update_post(
        post_id=str(post_id), 
        user_id=current_user.id,
        data=payload
    )
    
    return success_response(
        data=updated_post.model_dump(mode='json'),
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