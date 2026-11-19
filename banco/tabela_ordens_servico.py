from datetime import datetime

from flask import flash
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from database import OrdemServico, db_session


def select_todas():
    ordens_sql = select(OrdemServico).order_by(OrdemServico.id.asc())
    return db_session.execute(ordens_sql).scalars().all()


def salvar(os_id, responsavel_id, descricao, status_os, prioridade, custo_total, data_solicitacao, data_execucao):
    try:
        if not descricao or not descricao.strip():
            flash("Preencha a descrição da ordem de serviço", "error")
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
            prioridade=prioridade or "Média",
            custo_total=int(custo_total) if custo_total not in (None, "") else 0,
            data_solicitacao=data_solicitacao,
            data_execucao=data_execucao,
        )

        db_session.add(ordem)
        db_session.commit()
        flash("Ordem de serviço cadastrada com sucesso", "success")
        return True
    except SQLAlchemyError as e:
        db_session.rollback()
        flash("Erro ao cadastrar ordem de serviço no banco de dados", "error")
        print(f"Erro de Banco (Ordem de Serviço): {e}")
        return False
    except ValueError as e:
        db_session.rollback()
        flash("Datas inválidas. Informe as datas no formato correto", "error")
        print(f"Erro de valor (Ordem de Serviço): {e}")
        return False
    except Exception as e:
        db_session.rollback()
        flash("Erro inesperado ao cadastrar ordem de serviço", "error")
        print(f"Erro Inesperado (Ordem de Serviço): {e}")
        return False


def select_quantidade_total():
    ordens_sql = select(func.count(OrdemServico.id))
    qtd_total = db_session.execute(ordens_sql).scalar()
    return qtd_total


def select_ordem_status():
    ordens_sql = select(OrdemServico.status_os, func.count(OrdemServico.id)).group_by(OrdemServico.status_os).order_by(OrdemServico.status_os.asc())
    ordens = db_session.execute(ordens_sql).all()
    return ordens

def select_ordem_id(ordem_id):
    ordem_sql = select(OrdemServico).where(OrdemServico.id == int(ordem_id))
    ordem = db_session.execute(ordem_sql).scalar()
    return ordem