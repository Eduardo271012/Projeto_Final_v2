from sqlalchemy import func, select

from database import Usuario, db_session


def select_comuns():
    consulta = (
        select(Usuario)
        .where(Usuario.papel == "usuario")
        .order_by(Usuario.id.asc())
    )
    return db_session.execute(consulta).scalars().all()


def select_quantidade_comuns():
    consulta = select(func.count(Usuario.id)).where(Usuario.papel == "usuario")
    return db_session.execute(consulta).scalar_one()
