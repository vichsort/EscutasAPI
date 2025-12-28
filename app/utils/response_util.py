from flask import jsonify

class APIError(Exception):
    """
    Classe base para todos os erros da aplicação.
    Permite lançar erros com mensagem e status code específicos.
    Ex: raise APIError("Álbum não encontrado", 404)
    """
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(message)
        
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['status'] = 'error'
        rv['message'] = self.message
        return rv

def success_response(data=None, message="Success", status_code=200):
    """
    Padroniza o envelope de resposta de sucesso.
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
    """
    return jsonify({
        "status": "success",
        "message": message,
        "data": pagination.items, 
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
    Padroniza erros da API gerados manualmente.
    """
    rv = dict(payload or ())
    rv['status'] = 'error'
    rv['message'] = message
    return jsonify(rv), status_code

def handle_exception(e):
    """
    Handler global para capturar APIError e erros genéricos.
    """
    if isinstance(e, APIError):
        return jsonify(e.to_dict()), e.status_code
    
    # Se for um erro desconhecido, retorna 500 genérico mas mantém JSON
    print(f"Erro Interno não tratado: {e}") # Log simples para debug
    return jsonify({"status": "error", "message": "Internal Server Error"}), 500