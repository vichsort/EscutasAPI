from flask import jsonify

class APIError(Exception):
    """
    Classe base para todos os erros da aplicação.
    Permite lançar erros com mensagem e status code específicos.
    Ex: raise APIError("Álbum não encontrado", 404)
    """
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = True
        rv['message'] = self.message
        # Podemos adicionar código de erro interno aqui se quiser (ex: 'ERR_001')
        return rv

def success_response(data=None, message="Success", status_code=200):
    """
    Padroniza o envelope de resposta de sucesso.
    Sempre retornará: { "data": ..., "message": ..., "status": "success" }
    """
    response = {
        "status": "success",
        "message": message,
        "data": data
    }
    return jsonify(response), status_code

def paginated_response(pagination, message="Success"):
    """
    Transforma um objeto Pagination do SQLAlchemy em resposta JSON padrão.
    
    Args:
        pagination: Objeto retornado por query.paginate()
        message: Mensagem de sucesso
    """
    return jsonify({
        "status": "success",
        "message": message,
        "data": [item.to_dict() for item in pagination.items],
        "meta": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200

def error_response(message, status_code=400, payload=None):
    """
    Padroniza erros da API.
    """
    rv = dict(payload or ())
    rv['error'] = True
    rv['message'] = message
    return jsonify(rv), status_code

def handle_exception(e):
    """
    Handler global para capturar APIError e erros genéricos.
    """
    if isinstance(e, APIError):
        return jsonify(e.to_dict()), e.status_code
    
    # Se for um erro desconhecido (bug no código), escondemos os detalhes em Prod
    # Mas aqui vamos retornar 500 genérico
    return jsonify({"error": True, "message": "Internal Server Error"}), 500