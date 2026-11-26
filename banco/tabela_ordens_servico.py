from datetime import datetime
import unicodedata
import re
from flask import flash
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from database import (
    Equipamento,
    HistoricoOrdemServico,
    OrdemServico,
    OrdemServicoEquipamento,
    Setor,
    Usuario,
    db_session,
)

CATEGORIAS_OS = ("Manutenção", "Limpeza", "Elétrica", "Hidráulica", "Infraestrutura")
STATUS_OS = ("Aberta", "Em andamento", "Pausada", "Concluída", "Cancelada")
ROTULOS_HISTORICO = {
    "identificacao": "Identificação",
    "responsavel_id": "Funcionário responsável",
    "tecnico_responsavel_id": "Técnico responsável",
    "setor_id": "Setor",
    "categoria": "Categoria",
    "descricao": "Descrição",
    "status_os": "Status",
    "prioridade": "Prioridade",
    "custo_total": "Custo estimado",
    "data_solicitacao": "Data da solicitação",
    "data_execucao": "Data da execução",
    "equipamentos": "Equipamentos",
}


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
    data = datetime.now().strftime("%Y-%d-%H%S")
    nfkd = unicodedata.normalize('NFKD', usuario)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    nome = re.sub(r'[^a-zA-Z0-9]', '', sem_acento).lower()
    return f"{data}-{nome[:17]}"


def capturar_estado_historico(ordem, equipamentos_ids=None):
    if equipamentos_ids is None:
        equipamentos_ids = [
            associacao.equipamento_id
            for associacao in ordem.equipamentos_associados
        ]
    equipamentos_ids = sorted(set(equipamentos_ids))

    responsavel = db_session.get(Usuario, ordem.responsavel_id) if ordem.responsavel_id else None
    tecnico = (
        db_session.get(Usuario, ordem.tecnico_responsavel_id)
        if ordem.tecnico_responsavel_id
        else None
    )
    setor = db_session.get(Setor, ordem.setor_id) if ordem.setor_id else None
    equipamentos = db_session.execute(
        select(Equipamento).where(Equipamento.id.in_(equipamentos_ids))
    ).scalars().all() if equipamentos_ids else []
    equipamentos_por_id = {equipamento.id: equipamento for equipamento in equipamentos}
    nomes_equipamentos = [
        equipamentos_por_id[equipamento_id].nome
        if equipamento_id in equipamentos_por_id
        else f"Equipamento #{equipamento_id}"
        for equipamento_id in equipamentos_ids
    ]

    def formatar_data(data):
        return data.strftime("%d/%m/%Y") if data else "-"

    return {
        "identificacao": ordem.identificacao or "-",
        "responsavel_id": responsavel.nome if responsavel else "Não atribuído",
        "tecnico_responsavel_id": tecnico.nome if tecnico else "Não atribuído",
        "setor_id": setor.nome if setor else "Não atribuído",
        "categoria": ordem.categoria or "-",
        "descricao": ordem.descricao or "-",
        "status_os": ordem.status_os or "-",
        "prioridade": ordem.prioridade or "-",
        "custo_total": f"R$ {ordem.custo_total if ordem.custo_total is not None else 0}",
        "data_solicitacao": formatar_data(ordem.data_solicitacao),
        "data_execucao": formatar_data(ordem.data_execucao),
        "equipamentos": ", ".join(nomes_equipamentos) if nomes_equipamentos else "Nenhum",
    }


def registrar_historico(ordem_id, usuario_id, estado_anterior, estado_novo):
    for campo, rotulo in ROTULOS_HISTORICO.items():
        valor_anterior = estado_anterior.get(campo, "-")
        valor_novo = estado_novo.get(campo, "-")
        if valor_anterior != valor_novo:
            db_session.add(
                HistoricoOrdemServico(
                    ordem_servico_id=ordem_id,
                    usuario_id=usuario_id,
                    campo=rotulo,
                    valor_anterior=valor_anterior,
                    valor_novo=valor_novo,
                )
            )


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
    usuario_id=None,
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
        estado_inicial = capturar_estado_historico(ordem, equipamentos_ids)
        registrar_historico(
            ordem.id,
            usuario_id,
            {},
            estado_inicial,
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