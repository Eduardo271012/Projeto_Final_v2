from datetime import datetime
import unicodedata
import re
from flask import flash
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from database import (
    Equipamento,
    OrdemServico,
    OrdemServicoEquipamento,
    Setor,
    Usuario,
    db_session,
)

CATEGORIAS_OS = ("Manutenção", "Limpeza", "Elétrica", "Hidráulica", "Infraestrutura")
STATUS_OS = ("Aberta", "Em andamento", "Pausada", "Concluída", "Cancelada")


def validar_vinculos(
    categoria,
    setor_id,
    equipamentos_ids,
    ordem_atual=None,
    permitir_sem_equipamentos=False,
):
    if categoria not in CATEGORIAS_OS:
        flash("Selecione uma categoria válida para a ordem de serviço", "error")
        return None

    try:
        setor_id = int(setor_id)
    except (TypeError, ValueError):
        flash("Selecione um setor válido", "error")
        return None

    setor = db_session.get(Setor, setor_id)
    setor_atual_id = ordem_atual.setor_id if ordem_atual else None
    if not setor or (not setor.status_delete and setor.id != setor_atual_id):
        flash("Selecione um setor ativo", "error")
        return None

    equipamentos_atuais = {
        associacao.equipamento_id
        for associacao in ordem_atual.equipamentos_associados
    } if ordem_atual else set()
    if permitir_sem_equipamentos and not equipamentos_ids:
        equipamentos_ids = []
    else:
        equipamentos_ids = validar_equipamentos(equipamentos_ids, equipamentos_atuais)
        if equipamentos_ids is None:
            return None

    return setor_id, equipamentos_ids


def validar_equipamentos(equipamentos_ids, equipamentos_atuais=None):
    try:
        equipamentos_ids = list(dict.fromkeys(int(item) for item in equipamentos_ids))
    except (TypeError, ValueError):
        flash("Selecione equipamentos válidos", "error")
        return None

    if not equipamentos_ids:
        flash("Selecione pelo menos um equipamento", "error")
        return None

    equipamentos_atuais = equipamentos_atuais or set()
    equipamentos = db_session.execute(
        select(Equipamento).where(Equipamento.id.in_(equipamentos_ids))
    ).scalars().all()
    equipamentos_por_id = {equipamento.id: equipamento for equipamento in equipamentos}
    if len(equipamentos_por_id) != len(equipamentos_ids) or any(
        not equipamentos_por_id[equipamento_id].status_delete
        and equipamento_id not in equipamentos_atuais
        for equipamento_id in equipamentos_ids
    ):
        flash("Selecione apenas equipamentos ativos", "error")
        return None

    return equipamentos_ids


def validar_tecnico(tecnico_responsavel_id, tecnico_atual_id=None):
    if tecnico_responsavel_id in (None, ""):
        return None
    try:
        tecnico_responsavel_id = int(tecnico_responsavel_id)
    except (TypeError, ValueError):
        flash("Selecione um técnico válido", "error")
        return False

    tecnico = db_session.get(Usuario, tecnico_responsavel_id)
    if (
        not tecnico
        or tecnico.papel != "tecnico"
        or (not tecnico.ativo and tecnico.id != tecnico_atual_id)
    ):
        flash("Selecione um técnico ativo", "error")
        return False
    return tecnico_responsavel_id


def select_todas():
    ordens_sql = select(OrdemServico).order_by(OrdemServico.id.asc())
    return db_session.execute(ordens_sql).scalars().all()

def gerar_identificacao(usuario):
    data = datetime.now().strftime("%Y-%m-%d")
    nfkd = unicodedata.normalize('NFKD', usuario)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    nome = re.sub(r'[^a-zA-Z0-9]', '', sem_acento).lower()
    return f"{data}-{nome[:19]}"

def salvar(
    os_id,
    responsavel_id,
    tecnico_responsavel_id,
    identificacao,
    descricao,
    status_os,
    prioridade,
    custo_total,
    data_solicitacao,
    data_execucao,
    categoria,
    setor_id,
    equipamentos_ids,
    permitir_sem_equipamentos=False,
):
    try:
        if not descricao or not descricao.strip():
            flash("Preencha a descrição da ordem de serviço", "error")
            return False
        if status_os not in STATUS_OS:
            flash("Selecione um status válido para a ordem de serviço", "error")
            return False

        vinculos = validar_vinculos(
            categoria,
            setor_id,
            equipamentos_ids,
            permitir_sem_equipamentos=permitir_sem_equipamentos,
        )
        if vinculos is None:
            return False
        setor_id, equipamentos_ids = vinculos
        tecnico_responsavel_id = validar_tecnico(tecnico_responsavel_id)
        if tecnico_responsavel_id is False:
            return False

        try:
            custo_total = int(custo_total) if custo_total not in (None, "") else 0
        except ValueError:
            flash("O custo estimado deve ser um número inteiro não negativo", "error")
            return False
        if custo_total < 0:
            flash("O custo estimado não pode ser negativo", "error")
            return False

        data_solicitacao = (
            datetime.strptime(data_solicitacao, "%Y-%m-%d").date() if data_solicitacao else None
        )
        data_execucao = (
            datetime.strptime(data_execucao, "%Y-%m-%d").date() if data_execucao else None
        )
        if data_solicitacao and data_execucao and data_execucao < data_solicitacao:
            flash("A data de execução não pode ser anterior à data da solicitação", "error")
            return False

        ordem = OrdemServico(
            id=os_id or None,
            responsavel_id=int(responsavel_id) if responsavel_id not in (None, "") else None,
            tecnico_responsavel_id=(
                tecnico_responsavel_id
            ),
            setor_id=setor_id,
            identificacao=identificacao,
            categoria=categoria,
            descricao=descricao.strip(),
            status_os=status_os or "Aberta",
            prioridade=prioridade or "Média",
            custo_total=custo_total,
            data_solicitacao=data_solicitacao,
            data_execucao=data_execucao,
        )

        db_session.add(ordem)
        db_session.flush()
        db_session.add_all(
            OrdemServicoEquipamento(
                os_id=ordem.id,
                equipamento_id=equipamento_id,
                quantidade=1,
            )
            for equipamento_id in equipamentos_ids
        )
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
        flash("Datas ou valores inválidos. Verifique os dados informados", "error")
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

def select_ordens_ativas():
    ordens_sql = (
        select(OrdemServico).
        where(OrdemServico.status_delete == 1)
    )
    ordens_ativas = db_session.execute(ordens_sql).scalars().all()
    return ordens_ativas

def select_ordens_excluidas():
    ordens_sql = (
        select(OrdemServico).
        where(OrdemServico.status_delete == 0)
    )
    ordens_excluidas = db_session.execute(ordens_sql).scalars().all()
    return ordens_excluidas