import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class MonthlyMeta(db.Model):
    """
    Armazena metadados personalizados para o calendário do usuário, 
    como o título temático do mês.
    """
    __tablename__ = 'monthly_meta'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(30), nullable=False)
    user = db.relationship('User', backref=db.backref('monthly_metas', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'month', 'year', name='uix_user_month_year_meta'),
    )

    def to_dict(self):
        return {
            "month": self.month,
            "year": self.year,
            "title": self.title
        }