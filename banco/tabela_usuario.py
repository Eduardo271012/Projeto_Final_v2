from sqlalchemy import func, select

from database import Usuario, db_session


def select_comuns(ativos=True):
    consulta = (
        select(Usuario)
        .where(Usuario.papel == "usuario")
    )
    if ativos:
        consulta = consulta.where(Usuario.ativo.is_(True))
    return db_session.execute(consulta.order_by(Usuario.id.asc())).scalars().all()


def select_comuns_para_atribuicao(responsavel_atual_id=None):
    consulta = (
        select(Usuario)
        .where(Usuario.papel == "usuario")
        .where(
            (Usuario.ativo.is_(True))
            | (Usuario.id == responsavel_atual_id)
        )
        .order_by(Usuario.ativo.desc(), Usuario.nome.asc())
    )
    return db_session.execute(consulta).scalars().all()


def select_tecnicos_para_atribuicao(tecnico_atual_id=None):
    consulta = (
        select(Usuario)
        .where(Usuario.papel == "tecnico")
        .where(
            (Usuario.ativo.is_(True))
            | (Usuario.id == tecnico_atual_id)
        )
        .order_by(Usuario.ativo.desc(), Usuario.nome.asc())
    )
    return db_session.execute(consulta).scalars().all()


def select_quantidade_comuns():
    consulta = select(func.count(Usuario.id)).where(
        Usuario.papel == "usuario",
        Usuario.ativo.is_(True),
    )
    return db_session.execute(consulta).scalar_one()
