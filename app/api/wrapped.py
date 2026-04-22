from flask import Blueprint, request
from app.services import WrappedService
from app.utils import success_response, error_response, require_auth
from app.exceptions import BusinessRuleError
from datetime import datetime

wrapped_bp = Blueprint('wrapped', __name__, url_prefix='/api/wrapped')

@wrapped_bp.route('/generate-monthly', methods=['POST'])
@require_auth
def generate_monthly_wrapped(current_user):
    """
    Gera o Wrapped mensal do usuário logado: 
    Cria a playlist no Spotify e salva um rascunho no Blog.
    
    Espera um JSON: {"month": 4, "year": 2026}
    """
    data = request.get_json() or {}
    
    # Se o Front-end não mandar o mês/ano, assumimos o mês atual por padrão
    hoje = datetime.now()
    month = data.get('month', hoje.month)
    year = data.get('year', hoje.year)

    try:
        result = WrappedService.generate_wrapped(
            user_id=current_user.id,
            month=month,
            year=year
        )

        return success_response(
            data=result,
            message=f"Wrapped de {month}/{year} gerado com sucesso! O rascunho está pronto no seu blog."
        )

    except BusinessRuleError as e:
        return error_response(message=str(e), status_code=400)
    except Exception as e:
        print(f"Erro Crítico no Wrapped: {e}")
        return error_response("Ocorreu um erro ao gerar o seu Wrapped. Tente novamente mais tarde.", status_code=500)