from app.services.curation_service import CurationService
from app.services.spotify_service import SpotifyService
from app.models import AlbumReview, UserPlatinum
from app.utils import clean_album_title, is_canonical_album
from app.exceptions import SpotifyAPIError, ResourceNotFoundError
from spotipy.exceptions import SpotifyException
from app.extensions import db

class ArtistService:

    @staticmethod
    def get_platinum_progress(user, artist_id: str):
        """
        Calcula o progresso de Platina de um usuário para um artista específico.
        """
        sp = SpotifyService.get_client(user)

        try:
            # Pega os dados básicos do artista
            artist_info = sp.artist(artist_id)
            artist_name = artist_info['name']

            # Busca TODA a discografia de estúdio (paginada)
            albums = []
            results = sp.artist_albums(artist_id, album_type='album', limit=50)
            albums.extend(results['items'])
            
            while results['next']:
                results = sp.next(results)
                albums.extend(results['items'])

            # Pega as decisões da comunidade para todos esses IDs de uma vez
            spotify_ids = [a['id'] for a in albums]
            community_overrides = CurationService.get_community_overrides(spotify_ids)

            # Vamos agrupar os álbuns pelo 'nome limpo'.
            # Se o Yes tem 4 edições de "Close to the Edge", elas viram 1 item só aqui.
            canonical_discography = {}

            for item in albums:
                if item.get('album_type') == 'compilation':
                    continue

                raw_name = item['name']
                album_id = item['id']
                clean_name = clean_album_title(raw_name)

                # Veredito: Regex vs Comunidade
                regex_decision = is_canonical_album(raw_name)
                is_canonical = community_overrides.get(album_id, regex_decision)

                if clean_name not in canonical_discography:
                    canonical_discography[clean_name] = {
                        "clean_name": clean_name,
                        "cover_url": item['images'][0]['url'] if item['images'] else None,
                        "release_date": item['release_date'],
                        "is_canonical": is_canonical,
                        "versions": [album_id] # Guarda TODOS os IDs do Spotify que representam esse álbum
                    }
                else:
                    canonical_discography[clean_name]["versions"].append(album_id)
                    # Se qualquer versão do álbum for canônica, o álbum como um todo é necessário pra platina.
                    if is_canonical:
                        canonical_discography[clean_name]["is_canonical"] = True

            # Filtra apenas os álbuns que sobraram na peneira (A Discografia "Core")
            required_albums = {
                name: data for name, data in canonical_discography.items() 
                if data["is_canonical"]
            }

            # Busca as Reviews do Usuário
            all_required_version_ids = []
            for data in required_albums.values():
                all_required_version_ids.extend(data["versions"])

            # O usuário avaliou algum desses IDs?
            user_reviews = AlbumReview.query.filter(
                AlbumReview.user_id == user.id,
                AlbumReview.spotify_album_id.in_(all_required_version_ids)
            ).all()

            reviewed_spotify_ids = {r.spotify_album_id for r in user_reviews}

            # Cruza os dados e gera a resposta
            progress_list = []
            completed_count = 0

            for clean_name, data in required_albums.items():
                # Se o usuário avaliou QUALQUER versão desse álbum (Remaster, Deluxe, normal), tá valendo
                is_completed = any(vid in reviewed_spotify_ids for vid in data["versions"])
                
                if is_completed:
                    completed_count += 1

                progress_list.append({
                    "clean_name": clean_name,
                    "cover_url": data["cover_url"],
                    "release_date": data["release_date"][:4], # Só o ano (ex: 1969)
                    "is_completed": is_completed
                })
            
            # Ordena a discografia por ano de lançamento, do mais novo ao mais antigo
            progress_list.sort(key=lambda x: x['release_date'], reverse=True)

            total_required = len(required_albums)
            percentage = round((completed_count / total_required) * 100) if total_required > 0 else 0
            is_platinum = (total_required > 0) and (completed_count == total_required)

            total_required = len(required_albums)
            percentage = round((completed_count / total_required) * 100) if total_required > 0 else 0
            is_platinum = (total_required > 0) and (completed_count == total_required)

            # Verifica se o usuário já tem essa medalha no banco
            existing_plat = UserPlatinum.query.filter_by(
                user_id=user.id, 
                spotify_artist_id=artist_id
            ).first()

            if is_platinum:
                if not existing_plat:
                    # Bateu 100% e não tinha? entrega medalha
                    new_plat = UserPlatinum(
                        user_id=user.id,
                        spotify_artist_id=artist_id,
                        artist_name=artist_name,
                        artist_image_url=artist_info['images'][0]['url'] if artist_info['images'] else None
                    )
                    db.session.add(new_plat)
                    db.session.commit()
            else:
                if existing_plat:
                    # Lançaram álbum novo e ele não ouviu? tira medalha
                    db.session.delete(existing_plat)
                    db.session.commit()

            return {
                "artist": {
                    "id": artist_id,
                    "name": artist_name,
                    "image_url": artist_info['images'][0]['url'] if artist_info['images'] else None
                },
                "stats": {
                    "total_required": total_required,
                    "completed_count": completed_count,
                    "percentage": percentage,
                    "is_platinum": is_platinum
                },
                "discography": progress_list
            }

        except SpotifyException as e:
            if e.http_status == 404:
                raise ResourceNotFoundError("Artista")
            raise SpotifyAPIError(f"Erro ao buscar artista no Spotify: {e.msg}")