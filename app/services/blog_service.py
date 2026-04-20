from datetime import datetime, timezone
from app.extensions import db
from app.models import BlogPost, BlogPostMention
from app.exceptions import ResourceNotFoundError, AuthorizationError
from app.schemas import PostCreate, PostUpdate, BlogPostDetail, PaginatedBlogPostResponse, BlogPostList
from app.utils import generate_unique_slug, sync_post_mentions

class BlogService:
    @staticmethod
    def _get_post_and_verify_author(post_id, user_id):
        """Busca o post pela sintaxe nova e garante que o usuário é o dono."""
        post = db.session.get(BlogPost, post_id)
        
        if not post:
            raise ResourceNotFoundError("Post") 

        if str(post.user_id) != str(user_id):
            raise AuthorizationError("Você não tem permissão para realizar esta ação.")
            
        return post

    @staticmethod
    def create_post(user, data: PostCreate) -> BlogPostDetail:
        """
        Cria um novo post. 
        As menções polimórficas devem vir no array 'mentions'.
        """
        base_slug_text = data.slug if data.slug else data.title
        slug = generate_unique_slug(base_slug_text, BlogPost, db.session)

        post = BlogPost(
            user_id=user.id,
            title=data.title,
            slug=slug,
            summary=data.summary,
            content=data.content,
            cover_image_url=data.cover_image_url,
            status='DRAFT'
        )

        db.session.add(post)
        db.session.flush()

        if data.mentions:
            sync_post_mentions(post.id, data.mentions, db.session, BlogPostMention)

        db.session.commit()
        return BlogPostDetail.model_validate(post)

    @staticmethod
    def update_post(post_id, user_id, data: PostUpdate) -> BlogPostDetail:
        """Atualiza o post e sincroniza as menções."""
        post = BlogService._get_post_and_verify_author(post_id, user_id)

        update_data = data.model_dump(exclude_unset=True)

        if 'title' in update_data: post.title = update_data['title']
        if 'summary' in update_data: post.summary = update_data['summary']
        if 'content' in update_data: post.content = update_data['content']
        if 'cover_image_url' in update_data: post.cover_image_url = update_data['cover_image_url']

        if 'status' in update_data:
            if update_data['status'] == 'PUBLISHED' and post.status != 'PUBLISHED':
                post.published_at = datetime.now(timezone.utc)
            post.status = update_data['status']

        if data.mentions is not None:
            sync_post_mentions(post.id, data.mentions, db.session, BlogPostMention)

        db.session.commit()
        return BlogPostDetail.model_validate(post)

    @staticmethod
    def get_post_by_slug(slug, public_only=True) -> BlogPostDetail:
        """Busca para leitura (Frontend público)"""
        query = BlogPost.query.filter_by(slug=slug)
        
        if public_only:
            query = query.filter_by(status='PUBLISHED')
            
        post = query.first()
        if not post:
            raise ResourceNotFoundError("Post")

        return BlogPostDetail.model_validate(post)

    @staticmethod
    def list_posts(page=1, per_page=10, public_only=True) -> PaginatedBlogPostResponse:
        """Listagem paginada e blindada pelo Pydantic"""
        query = BlogPost.query.order_by(BlogPost.created_at.desc())
        
        if public_only:
            query = query.filter_by(status='PUBLISHED')
            
        paginacao = query.paginate(page=page, per_page=per_page, error_out=False)

        return PaginatedBlogPostResponse(
            items=[BlogPostList.model_validate(p) for p in paginacao.items],
            total=paginacao.total,
            page=paginacao.page,
            pages=paginacao.pages
        )

    @staticmethod
    def delete_post(post_id, user_id):
        """Deleta um post (CASCADE deleta as menções junto!)"""
        post = BlogService._get_post_and_verify_author(post_id, user_id)
            
        db.session.delete(post)
        db.session.commit()
        return True