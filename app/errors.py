from flask import jsonify
from pydantic import ValidationError as PydanticValidationError
from app.utils.response_util import APIError, handle_exception
from app.exceptions import EscutasError, DataValidationError 

def register_error_handlers(app):
    app.register_error_handler(APIError, handle_exception)

    @app.errorhandler(EscutasError)
    def handle_escutas_error(e):
        response = jsonify(e.to_dict())
        response.status_code = e.status_code
        return response

    @app.errorhandler(PydanticValidationError)
    def handle_pydantic_error(e):
        # Filtra apenas os dados seguros (strings/listas) para o JSON não engasgar
        safe_errors = []
        for err in e.errors():
            safe_errors.append({
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type")
            })
            
        custom_error = DataValidationError(errors=safe_errors)
        response = jsonify(custom_error.to_dict())
        response.status_code = custom_error.status_code
        return response

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"status": "error", "message": "Você está indo rápido demais!", "description": e.description}), 429

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "message": "Rota ou recurso não encontrado."}), 404

    app.register_error_handler(Exception, handle_exception)