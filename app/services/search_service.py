from app.extensions import cache, db
from app.services.spotify_service import SpotifyService
from app.schemas import SearchResult
from app.models import AlbumReview
import sqlalchemy as sa

class SearchService:

    @staticmethod
    @cache.memoize(timeout=300)
    def quick_search(query: str, limit_per_type: int = 3) -> list[SearchResult]:
        """
        Realiza uma busca combinada no Spotify e retorna uma lista 
        padronizada de SearchResult.
        """
        if not query or len(query) < 2:
            return []

        sp = SpotifyService.get_client(user=None)
        if not sp:
            return []

        results = []

        try:
            # Busca no Spotify (Artistas, Álbuns e Faixas de uma vez só)
            # O limit é aplicado a CADA tipo.
            search_data = sp.search(q=query, type='artist,album,track', limit=limit_per_type)

            # artistas
            for item in search_data.get('artists', {}).get('items', []):
                results.append(SearchResult(
                    id=item['id'],
                    name=item['name'],
                    type='ARTIST',
                    image_url=item['images'][0]['url'] if item['images'] else None,
                    subtitle="Artista"
                ))

            # albuns
            for item in search_data.get('albums', {}).get('items', []):
                results.append(SearchResult(
                    id=item['id'],
                    name=item['name'],
                    type='ALBUM',
                    image_url=item['images'][0]['url'] if item['images'] else None,
                    subtitle=item['artists'][0]['name'] if item['artists'] else "Álbum"
                ))

            # tracks
            for item in search_data.get('tracks', {}).get('items', []):
                results.append(SearchResult(
                    id=item['id'],
                    name=item['name'],
                    type='TRACK',
                    image_url=item['album']['images'][0]['url'] if item['album']['images'] else None,
                    subtitle=f"Música de {item['artists'][0]['name']}"
                ))

            # também pode mencionar reviews específicas:
            reviews = db.session.execute(
               sa.select(AlbumReview).where(AlbumReview.album_name.ilike(f'%{query}%')).limit(limit_per_type)
            ).scalars().all()
            for r in reviews:
               results.append(SearchResult(id=str(r.id), name=r.album_name, type='REVIEW', subtitle="Sua Review"))

        except Exception as e:
            print(f"Erro na busca rápida: {e}")
            
        return results