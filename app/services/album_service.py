from app.extensions import cache
from app.services.spotify_service import SpotifyService

class AlbumService:
    
    @staticmethod
    @cache.memoize(timeout=3600)  # Cache de 1 hora para pesquisas
    def search_albums(user, query):
        """
        Busca álbuns no Spotify pelo nome.
        Retorna uma lista simplificada.
        """
        sp = SpotifyService.get_client(user)
        if not sp: return []

        try:
            results = sp.search(q=query, type='album', limit=20)
            albums_data = []
            
            for item in results['albums']['items']:
                # Reutilizamos aquele helper privado que criámos no SpotifyService
                # (Terás de tornar o método _extract_album_data público ou copiar a lógica. 
                # Para facilitar, vamos copiar a lógica simples aqui ou importar se mudarmos lá).
                
                # Lógica simples de extração para busca:
                if item.get('album_type') == 'compilation': continue # Opcional
                
                cover = item['images'][0]['url'] if item['images'] else None
                
                albums_data.append({
                    "spotify_id": item['id'],
                    "name": item['name'],
                    "artist": ", ".join([artist['name'] for artist in item['artists']]),
                    "cover_url": cover,
                    "release_date": item['release_date']
                })
                
            return albums_data

        except Exception as e:
            print(f"Erro na busca de álbuns: {e}")
            return []

    @staticmethod
    @cache.memoize(timeout=604800)  # Cache de 7 DIAS (Heavy Load)
    def get_album_details(user, album_id):
        """
        Busca os detalhes completos (incluindo todas as faixas).
        Esta é a chamada pesada que queremos evitar repetir.
        """
        sp = SpotifyService.get_client(user)
        if not sp: return None

        try:
            # Pega o álbum completo
            album = sp.album(album_id)
            
            # Formata as faixas
            tracks_clean = []
            for track in album['tracks']['items']:
                tracks_clean.append({
                    "id": track['id'],
                    "name": track['name'],
                    "track_number": track['track_number'],
                    "duration_ms": track['duration_ms'],
                    "preview_url": track['preview_url'] # Pode ser null, mas é bom ter
                })

            cover = album['images'][0]['url'] if album['images'] else None

            # Monta o objeto final limpo
            return {
                "spotify_id": album['id'],
                "name": album['name'],
                "artist": ", ".join([a['name'] for a in album['artists']]),
                "cover_url": cover,
                "release_date": album['release_date'],
                "total_tracks": album['total_tracks'],
                "label": album.get('label'), # Gravadora (Curiosidade)
                "tracks": tracks_clean
            }

        except Exception as e:
            print(f"Erro ao detalhar álbum {album_id}: {e}")
            return None