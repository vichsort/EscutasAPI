from typing import List, Optional
from sqlalchemy import or_
from app.models.user import User
from app.schemas.user import UserPublic, UserProfile

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
        user = User.query.get(user_uuid)
        if not user:
            return None

        user_dto = UserProfile.model_validate(user)
        
        if user.created_at:
            user_dto.joined_at = user.created_at.isoformat()
            
        return user_dto