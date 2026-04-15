from app.extensions import db
from app.models.curation import AlbumCurationVote
from app.constants import CURATION_THRESHOLD

class CurationService:

    @staticmethod
    def register_vote(user_id, spotify_album_id: str, is_canonical: bool):
        """
        Registra ou atualiza o voto de um usuário.
        """
        vote = AlbumCurationVote.query.filter_by(
            user_id=user_id, 
            spotify_album_id=spotify_album_id
        ).first()

        if vote:
            vote.is_canonical = is_canonical
        else:
            vote = AlbumCurationVote(
                user_id=user_id,
                spotify_album_id=spotify_album_id,
                is_canonical=is_canonical
            )
            db.session.add(vote)
            
        db.session.commit()
        return vote

    @staticmethod
    def get_community_overrides(spotify_ids: list) -> dict:
        """
        Recebe uma lista de IDs do Spotify.
        Retorna um dicionário com a decisão da comunidade caso o threshold tenha sido atingido.
        Ex: {'id_do_album': False} -> A comunidade votou que NÃO é canônico.
        """
        if not spotify_ids:
            return {}

        # Busca todos os votos para esses álbuns
        votes = AlbumCurationVote.query.filter(
            AlbumCurationVote.spotify_album_id.in_(spotify_ids)
        ).all()

        # Conta os votos: True = +1 (A favor), False = -1 (Contra)
        vote_counts = {}
        for v in votes:
            if v.spotify_album_id not in vote_counts:
                vote_counts[v.spotify_album_id] = 0
            
            vote_counts[v.spotify_album_id] += 1 if v.is_canonical else -1

        # Verifica quem atingiu o Threshold
        overrides = {}
        for album_id, net_votes in vote_counts.items():
            if net_votes >= CURATION_THRESHOLD:
                overrides[album_id] = True  # Comunidade decidiu FORÇAR como Platina
            elif net_votes <= -CURATION_THRESHOLD:
                overrides[album_id] = False # Comunidade decidiu REMOVER da Platina
                
        return overrides