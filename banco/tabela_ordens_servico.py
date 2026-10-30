from flask import flash

from database import OrdemServico, db_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func
from datetime import datetime


def select_todas():
    # Busca todas as OS ativas trazendo os relacionamentos de cliente e funcionário carregados
    ordens_sql = select(OrdemServico)
    ordens = db_session.execute(ordens_sql).scalars().all()
    return ordens


def salvar(cliente_id, responsavel_id, descricao, status_os, prioridade, custo_total, data_solicitacao, data_execucao):
    try:
        # Tratamento de datas vindo de strings do HTML input date para objetos date do Python
        dt_sol = datetime.strptime(data_solicitacao, "%Y-%m-%d").date() if data_solicitacao else None
        dt_exe = datetime.strptime(data_execucao, "%Y-%m-%d").date() if data_execucao else None

        custo = int(custo_total) if custo_total else 0

        ordem_nova = OrdemServico(
            responsavel_id=int(responsavel_id) if responsavel_id else None,
            descricao=descricao,
            status_os=status_os,
            prioridade=prioridade,
            custo_total=custo,
            data_solicitacao=dt_sol,
            data_execucao=dt_exe
        )
        db_session.add(ordem_nova)
        db_session.commit()
        flash("Ordem de Serviço criada com sucesso!", "success")
        return True
    except SQLAlchemyError as e:
        db_session.rollback()
        print(f"Erro de Banco (OS): {e}")
        flash("Erro ao salvar ordem de serviço no banco local.", "error")
        return False
    except Exception as e:
        db_session.rollback()
        print(f"Erro Inesperado (OS): {e}")
        flash("Erro inesperado ao gerar OS.", "error")
        return False



def select_quantidade_total():
    ordens_servico_sql = select(func.count(OrdemServico.id))
    qtd_total = db_session.execute(ordens_servico_sql).scalar()
    return qtd_total