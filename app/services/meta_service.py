from app.extensions import db
from app.models import MonthlyMeta
from app.exceptions import BusinessRuleError

class MetaService:
    @staticmethod
    def set_monthly_title(user_id: str, month: int, year: int, title: str):
        """
        Define ou atualiza o título temático de um mês para o usuário (Upsert).
        """
        # Validações de segurança e regra de negócio
        if not title or len(title) > 30:
            raise BusinessRuleError("O título deve ter entre 1 e 30 caracteres.")
        if not (1 <= month <= 12):
            raise BusinessRuleError("Mês inválido.")

        # Busca pra ver se o cara já tem um título nesse mês
        meta = MonthlyMeta.query.filter_by(user_id=user_id, month=month, year=year).first()
        
        if meta:
            # Upsert: Já existe? Só atualiza o texto!
            meta.title = title
        else:
            # Não existe? Cria um novo do zero.
            meta = MonthlyMeta(user_id=user_id, month=month, year=year, title=title)
            db.session.add(meta)
        
        db.session.commit()
        return meta

    @staticmethod
    def get_monthly_title(user_id: str, month: int, year: int) -> str:
        """
        Busca o título de um mês. Retorna None se não existir.
        """
        meta = MonthlyMeta.query.filter_by(user_id=user_id, month=month, year=year).first()
        return meta.title if meta else None