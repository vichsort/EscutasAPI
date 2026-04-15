import re
from datetime import datetime, timezone
from app.extensions import db
from app.models import BlogPost
from app.services.spotify_service import SpotifyService
from spotipy.exceptions import SpotifyException
from app.exceptions import (
    BusinessRuleError, 
    ResourceNotFoundError, 
    AuthorizationError, 
    SpotifyAPIError
)

class BlogService:
    TRACK_REGEX = r'spotify:track:([a-zA-Z0-9]{22})'

    @staticmethod
    def _enrich_content_with_metadata(content):
        """
        VARRE o texto procurando IDs do Spotify.
        BUSCA os dados na API em lotes (max 50 por vez).
        RETORNA um dicionário (Snapshot) para salvar no banco.
        """
        if not content:
            return {}

        track_ids = list(set(re.findall(BlogService.TRACK_REGEX, content)))
        
        if not track_ids:
            return {}

        metadata = {}
        sp = SpotifyService.get_client(user=None)

        if not sp:
            print("Aviso: Cliente Spotify não disponível para buscar metadados do Blog.")
            return {}

        try:
            # Agora o Spotify só aceita 50 tracks por vez no endpoint get_several_tracks.
            # Vamos fatiar a lista de IDs em pedaços (chunks) de 50.
            chunk_size = 50
            for i in range(0, len(track_ids), chunk_size):
                chunk = track_ids[i:i + chunk_size]
                response = sp.tracks(chunk)
                
                for track in response['tracks']:
                    if track:
                        metadata[track['id']] = {
                            "name": track['name'],
                            "artist": ", ".join([artist['name'] for artist in track['artists']]),
                            "album": track['album']['name'],
                            "cover_url": track['album']['images'][0]['url'] if track['album']['images'] else None,
                            "preview_url": track['preview_url']
                        }
                        
        except SpotifyException as e:
            raise SpotifyAPIError(f"Erro ao buscar metadados das faixas pro Blog: {e.msg}")

        return metadata

    @staticmethod
    def create_post(user, data):
        """Cria um novo post e gera o snapshot de metadados"""
        if BlogPost.query.filter_by(slug=data['slug']).first():
            raise BusinessRuleError("Este slug já está em uso. Escolha outro.")

        track_metadata = BlogService._enrich_content_with_metadata(data['content'])

        post = BlogPost(
            user_id=user.id,
            title=data['title'],
            slug=data['slug'],
            summary=data.get('summary'),
            content=data['content'],
            cover_image_url=data.get('cover_image_url'),
            related_review_id=data.get('related_review_id'),
            track_metadata=track_metadata,
            status='DRAFT'
        )

        db.session.add(post)
        db.session.commit()
        return post

    @staticmethod
    def update_post(post_id, user_id, data):
        """Atualiza post e REGENERA o snapshot se o texto mudou"""
        post = BlogPost.query.get(post_id)
        
        if not post:
            raise ResourceNotFoundError("Post") 

        # Verifica permissão (apenas o autor pode editar)
        if str(post.user_id) != str(user_id):
            raise AuthorizationError("Você não tem permissão para editar este post.")

        if 'title' in data: post.title = data['title']
        if 'summary' in data: post.summary = data['summary']
        if 'cover_image_url' in data: post.cover_image_url = data['cover_image_url']
        
        # Se mudou conteúdo, regenera metadata
        if 'content' in data and data['content'] != post.content:
            post.content = data['content']
            post.track_metadata = BlogService._enrich_content_with_metadata(post.content)

        # Se mudou status para PUBLISHED e não tinha data, seta agora
        if 'status' in data:
            if data['status'] == 'PUBLISHED' and post.status != 'PUBLISHED':
                post.published_at = datetime.now(timezone.utc)
            post.status = data['status']

        db.session.commit()
        return post

    @staticmethod
    def get_post_by_slug(slug, public_only=True):
        """Busca para leitura (Frontend público)"""
        query = BlogPost.query.filter_by(slug=slug)
        
        if public_only:
            query = query.filter_by(status='PUBLISHED')
            
        post = query.first()

        return post

    @staticmethod
    def list_posts(page=1, per_page=10, public_only=True):
        """Listagem paginada"""
        query = BlogPost.query.order_by(BlogPost.created_at.desc())
        
        if public_only:
            query = query.filter_by(status='PUBLISHED')
            
        return query.paginate(page=page, per_page=per_page, error_out=False)