from datetime import datetime

from flask import flash
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from database import OrdemServico, db_session


def select_todas():
    ordens_sql = select(OrdemServico).order_by(OrdemServico.id.desc())
    return db_session.execute(ordens_sql).scalars().all()


def salvar(os_id, responsavel_id, descricao, status_os, prioridade, custo_total, data_solicitacao, data_execucao):
    try:
        if not descricao or not descricao.strip():
            flash("Preencha a descri??o da ordem de servi?o", "error")
            return False

        data_solicitacao = (
            datetime.strptime(data_solicitacao, "%Y-%m-%d").date() if data_solicitacao else None
        )
        data_execucao = (
            datetime.strptime(data_execucao, "%Y-%m-%d").date() if data_execucao else None
        )

        ordem = OrdemServico(
            id=os_id or None,
            responsavel_id=int(responsavel_id) if responsavel_id not in (None, "") else None,
            descricao=descricao.strip(),
            status_os=status_os or "Aberta",
            prioridade=prioridade or "M?dia",
            custo_total=int(custo_total) if custo_total not in (None, "") else 0,
            data_solicitacao=data_solicitacao,
            data_execucao=data_execucao,
        )

        db_session.add(ordem)
        db_session.commit()
        flash("Ordem de servi?o cadastrada com sucesso", "success")
        return True
    except SQLAlchemyError as e:
        db_session.rollback()
        flash("Erro ao cadastrar ordem de servi?o no banco de dados", "error")
        print(f"Erro de Banco (Ordem de Servi?o): {e}")
        return False
    except ValueError as e:
        db_session.rollback()
        flash("Datas inv?lidas. Informe as datas no formato correto", "error")
        print(f"Erro de valor (Ordem de Servi?o): {e}")
        return False
    except Exception as e:
        db_session.rollback()
        flash("Erro inesperado ao cadastrar ordem de servi?o", "error")
        print(f"Erro Inesperado (Ordem de Servi?o): {e}")
        return False


def select_quantidade_total():
    ordens_sql = select(func.count(OrdemServico.id))
    qtd_total = db_session.execute(ordens_sql).scalar()
    return qtd_total
