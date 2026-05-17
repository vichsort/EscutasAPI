from typing import List, Optional
from app.extensions import db
from sqlalchemy import or_
from app.models import User, Album, AlbumReview, UserPlatinum
from app.schemas import UserPublic, UserProfile,PlatinumTrophyOutput

class UserService:
    
    @staticmethod
    def search_users(query_str: str) -> List[UserPublic]:
        """
        Busca usuários por Nome (parcial) ou Spotify ID (exato).
        Retorna uma lista de objetos Pydantic UserPublic.
        """
        if not query_str:
            return []
            
        # Limpa espaços extras
        term = query_str.strip()
        
        # Query Híbrida:
        # 1. display_name CONTÉM o termo (case insensitive)
        # 2. OU spotify_id É IGUAL ao termo
        users = User.query.filter(
            or_(
                User.display_name.ilike(f'%{term}%'),
                User.spotify_id == term
            )
        ).limit(20).all()

        return [UserPublic.model_validate(user) for user in users]

    @staticmethod
    def get_user_profile(user_uuid: str) -> Optional[UserProfile]:
        """
        Busca um usuário específico pelo UUID.
        Retorna um objeto Pydantic UserProfile ou None.
        """
        user = db.session.get(User, user_uuid)
        
        if not user:
            return None
            
        user_dto = UserProfile.model_validate(user)
        
        if user.created_at:
            user_dto.joined_at = user.created_at.isoformat()
            
        return user_dto

    @staticmethod
    def get_user_platinums(user_id) -> list:
        """
        Busca dados de platina do usuário.
        Retorna total para platina, quanto foi completo e a porcentagem expressa, 
        """
        trophies = UserPlatinum.query.filter_by(user_id=user_id).order_by(UserPlatinum.achieved_at.desc()).all()
        artist_ids = [t.spotify_artist_id for t in trophies]

        total_per_artist = dict(
            db.session.query(Album.artist_spotify_id, db.func.count(Album.id))
            .filter(Album.artist_spotify_id.in_(artist_ids), Album.is_canonical == True)
            .group_by(Album.artist_spotify_id)
            .all()
        )

        reviewed_per_artist = dict(
            db.session.query(Album.artist_spotify_id, db.func.count(AlbumReview.id))
            .join(AlbumReview, AlbumReview.spotify_album_id == Album.spotify_album_id)
            .filter(
                Album.artist_spotify_id.in_(artist_ids),
                Album.is_canonical == True,
                AlbumReview.user_id == user_id
            )
            .group_by(Album.artist_spotify_id)
            .all()
        )

        data = []
        
        for t in trophies:
            aid = t.spotify_artist_id
            total = total_per_artist.get(aid, 0)
            completed = reviewed_per_artist.get(aid, 0)
            percentage = round((completed / total) * 100) if total > 0 else 100
            entry = PlatinumTrophyOutput.model_validate(t).model_dump()
            entry['total_required'] = total
            entry['completed_count'] = completed
            entry['percentage'] = percentage
            data.append(entry)

        return data