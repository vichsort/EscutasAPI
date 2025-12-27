from flask import Blueprint, redirect, request, jsonify, session, current_app
from app.services.spotify_service import SpotifyService
from app.extensions import db
from app.services.spotify_service import SpotifyService
from app.services.auth_service import AuthService
from app.models.user import User
import time

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/login')
def login():
    """
    Inicia o fluxo OAuth.
    Params (Saída): Redirect 302 para Spotify.
    """
    sp_oauth = SpotifyService.get_oauth_object()
    service = SpotifyService()
    return redirect(service.get_auth_url())

@auth_bp.route('/callback')
def callback():
    """
    Recebe o code e salva o token na sessão.
    Params (Entrada): ?code=XYZ
    """
    if 'error' in request.args:
        return jsonify({"error": request.args['error']}), 400
    
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Código de autorização não fornecido"}), 400

    try:
        # 2. Troca de Código por Token (SpotifyService)
        sp_oauth = SpotifyService.get_oauth_object()
        token_info = sp_oauth.get_access_token(code)
        
        # 3. Obtenção de Dados do Usuário (SpotifyService / Spotipy)
        import spotipy
        sp = spotipy.Spotify(auth=token_info['access_token'])
        spotify_user_data = sp.current_user()

        # 4. Regra de Negócio / Persistência (AuthService) <--- AQUI MUDOU
        # A rota não sabe se é insert ou update, o serviço resolve.
        user = AuthService.login_or_register_user(spotify_user_data, token_info)

        # 5. Gestão de Sessão (Responsabilidade da Rota)
        session.clear()
        session['_user_id'] = str(user.id)

        return jsonify({
            "message": "Login realizado com sucesso!",
            "user": user.display_name
        })

    except Exception as e:
        return jsonify({"error": "Falha no processo de login", "details": str(e)}), 500

@auth_bp.route('/me')
def me():
    """
    Verifica sessão ativa.
    Params (Saída): JSON { logged_in: bool, user: dict }
    """
    sp = SpotifyService().get_client()
    if not sp:
        return jsonify({"logged_in": False}), 401
    
    return jsonify({"logged_in": True, "user": sp.current_user()})