from flask import jsonify

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
    print(f"Erro Interno não tratado: {e}")
    return jsonify({"status": "error", "message": "Internal Server Error"}), 500