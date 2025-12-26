from flask import Blueprint, redirect, request, jsonify, session, current_app
from app.services.spotify_service import SpotifyService

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/login')
def login():
    """
    Inicia o fluxo OAuth.
    Params (Saída): Redirect 302 para Spotify.
    """
    service = SpotifyService()
    return redirect(service.get_auth_url())

@auth_bp.route('/callback')
def callback():
    """
    Recebe o code e salva o token na sessão.
    Params (Entrada): ?code=XYZ
    """
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400
        
    service = SpotifyService()
    token_info = service.get_token_from_code(code)
    session['token_info'] = token_info
    
    # Redireciona para o Frontend
    # temporariamente fora pra testar enquanto n tiver frontend
    # return redirect('http://localhost:5173/dashboard')

    # app/api/auth.py
    return jsonify({
        "message": "Login realizado com sucesso!",
        "user_uuid": session.get('_user_id'), # Só pra confirmar
        "note": "Copie o cookie 'session' no F12 -> Application -> Cookies"
    })

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