from app.extensions import db
from app.models.user import User

class AuthService:
    
    @staticmethod
    def login_or_register_user(spotify_user_data, token_info):
        """
        Lógica de negócio:
        1. Verifica se o usuário existe.
        2. Se não, cria.
        3. Se sim, apenas atualiza os tokens.
        4. Comita a transação de forma atômica.
        """
        try:
            spotify_id = spotify_user_data['id']
            user = User.query.filter_by(spotify_id=spotify_id).first()

            if not user:
                # Criação de novo usuário
                user = User(
                    spotify_id=spotify_id,
                    display_name=spotify_user_data.get('display_name'),
                    email=spotify_user_data.get('email')
                )
                db.session.add(user)
            
            # Atualiza tokens (seja usuário novo ou antigo)
            user.update_tokens(token_info)
            
            db.session.commit()
            return user

        except Exception as e:
            db.session.rollback()
            raise e