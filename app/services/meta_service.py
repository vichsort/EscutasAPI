from app.extensions import db
from app.models import MonthlyMeta, AlbumReview, UserMonthlyMeta
from app.exceptions import BusinessRuleError
from app.utils import generate_monthly_title

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

    @staticmethod
    def generate_automatic_monthly_title(user_id, month, year):
        """
        Analisa os géneros das reviews do utilizador no mês 
        e gera um título automático.
        """
        # Procura todas as reviews do utilizador naquele mês/ano
        from sqlalchemy import extract
        reviews = AlbumReview.query.filter(
            AlbumReview.user_id == user_id,
            extract('month', AlbumReview.created_at) == month,
            extract('year', AlbumReview.created_at) == year
        ).all()

        if not reviews:
            raise BusinessRuleError("Ainda não tens reviews este mês para gerar um título!")

        # Coleta todos os géneros (artist_genres é uma lista/JSON no banco)
        all_genres = []
        for r in reviews:
            if r.artist_genres:
                all_genres.extend(r.artist_genres)

        # Usa o nosso utilitário da Missão 1
        new_title = generate_monthly_title(all_genres)

        # Guarda ou atualiza na tabela Meta
        meta = UserMonthlyMeta.query.filter_by(
            user_id=user_id, month=month, year=year
        ).first()

        if not meta:
            meta = UserMonthlyMeta(user_id=user_id, month=month, year=year)
            db.session.add(meta)

        meta.title = new_title
        db.session.commit()

        return meta