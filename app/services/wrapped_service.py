from app.extensions import db
from app.models import User
from app.utils import get_monthly_summary, generate_monthly_post_content
from app.services.spotify_service import SpotifyService
from app.services.blog_service import BlogService
from app.schemas.blog import PostCreate
from app.exceptions import BusinessRuleError
from app.constants import MESES

class WrappedService:
    """
    O Maestro. 
    Coordena a extração de dados, a API do Spotify e a criação do rascunho no Blog.
    """

    @staticmethod
    def generate_wrapped(user_id: str, month: int, year: int):
        user = db.session.get(User, user_id)
        if not user:
            raise BusinessRuleError("Usuário não encontrado.")

        stats = get_monthly_summary(user_id, month, year, db.session)
        
        if not stats or stats['total_reviews'] == 0:
            raise BusinessRuleError(f"Você não possui avaliações suficientes em {month}/{year} para gerar um Wrapped.")

        sp = SpotifyService.get_client()
        
        best_album_data = sp.album(stats['best_album_id'])
        best_album_name = best_album_data['name']
        best_album_artist = best_album_data['artists'][0]['name']
        best_album_cover = best_album_data['images'][0]['url'] if best_album_data['images'] else None

        track_uris = []
        for album_id in stats['top_album_ids']:
            # Pegamos apenas a faixa número 1 do álbum para representar na playlist
            tracks_data = sp.album_tracks(album_id, limit=1)
            if tracks_data['items']:
                track_uris.append(tracks_data['items'][0]['uri'])

        # 4. Criar a Playlist no Spotify
        nome_mes = MESES.get(month, "Mês")
        playlist_name = f"Meus Favoritos: {nome_mes} / {year} - Escutas"
        playlist_desc = f"A nata do que eu ouvi em {nome_mes} de {year}. Curadoria gerada automaticamente."
        
        playlist_id = SpotifyService.create_user_playlist(user.spotify_id, playlist_name, playlist_desc)
        
        if playlist_id:
            SpotifyService.add_tracks_to_playlist(playlist_id, track_uris)
            playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        else:
            # Fallback caso dê erro na criação
            playlist_url = "https://open.spotify.com" 

        # 5. Chama o Ghost Writer para gerar o Texto Markdown
        title, summary, content = generate_monthly_post_content(
            month=month,
            year=year,
            stats=stats,
            best_album_name=best_album_name,
            best_album_artist=best_album_artist,
            playlist_url=playlist_url
        )

        # 6. Salva no Blog como Rascunho (DRAFT)
        # O pulo do gato: já enviamos a capa do álbum de ouro e a menção polimórfica!
        post_data = PostCreate(
            title=title,
            summary=summary,
            content=content,
            cover_image_url=best_album_cover,
            slug=None, # O gerador inteligente de slug fará o trabalho
            mentions=[
                {"target_type": "ALBUM", "target_id": stats['best_album_id'], "target_name": best_album_name}
            ]
        )

        draft_post = BlogService.create_post(user, post_data)

        # Retornamos o ID e o Slug do post recém-criado para o Front-end redirecionar o usuário
        return {
            "post_id": draft_post.id,
            "post_slug": draft_post.slug,
            "playlist_url": playlist_url
        }