from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from banco import tabela_equipamento, tabela_ordens_servico, tabela_setor, tabela_usuario
from database import (
    AuditoriaSistema,
    Equipamento,
    HistoricoOrdemServico,
    MensagemOrdemServico,
    OrdemServico,
    OrdemServicoEquipamento,
    SolicitacaoRestauracaoOS,
    Setor,
    Usuario,
    db_session,
)
from banco.auditoria import registrar_evento
from functools import wraps
from datetime import datetime, timedelta
from validate_docbr import CPF


app = Flask(__name__)
app.secret_key = "quarks-solucoes"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    usuario = db_session.get(Usuario, int(user_id))
    if usuario and not usuario.ativo:
        return None
    return usuario


def roles_required(*papeis_permitidos):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.papel not in papeis_permitidos:
                flash("Você não tem permissão para acessar esta página.", "error")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.context_processor
def solicitacoes_restauracao_pendentes():
    if current_user.is_authenticated and current_user.papel == "admin":
        total = db_session.execute(
            select(func.count(SolicitacaoRestauracaoOS.id)).where(
                SolicitacaoRestauracaoOS.status == "pendente"
            )
        ).scalar_one()
        return {"total_solicitacoes_restauracao": total}
    return {"total_solicitacoes_restauracao": 0}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()
        usuario_sql = select(Usuario).where(Usuario.email == email)
        usuario_resultado = db_session.execute(usuario_sql).scalar()

        if not usuario_resultado:
            flash("Falha na autenticação: E-mail não encontrado", "error")
            return redirect(url_for("login"))
        if not usuario_resultado.ativo:
            flash("Este usuário está inativo e não pode acessar o sistema", "error")
            return redirect(url_for("login"))
        if usuario_resultado and usuario_resultado.check_password(senha):
            login_user(usuario_resultado)
            flash(f"BEM-VINDO(A), {usuario_resultado.nome} ({usuario_resultado.papel})!😁", "welcome")
            return redirect(url_for("index"))
        else:
            flash("Falha na autenticação: E-mail e senha não encontrado", "error")

    return render_template(
        "login.html",
        registro= request.args.get("registro") == "True"

    )

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf = "".join(filter(str.isdigit, request.form.get("cpf", "")))
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()

        if not nome or not cpf or not email or not senha:
            flash("Preencha o nome, CPF, email e senha", "error")
            return redirect(url_for("registro"))
        if len(cpf) != 11 or not CPF().validate(cpf):
            flash("Informe um CPF válido", "error")
            return redirect(url_for("registro", registro="True"))
        usuario_sql = select(Usuario).where(Usuario.email == email)
        usuario_email = db_session.execute(usuario_sql).scalar_one_or_none()
        if usuario_email:
            flash("E-mail já cadastrado", "error")
            return redirect(url_for("registro"))
        cpf_sql = select(Usuario).where(Usuario.cpf == cpf)
        if db_session.execute(cpf_sql).scalar_one_or_none():
            flash("CPF já cadastrado", "error")
            return redirect(url_for("registro", registro="True"))
        try:
            novo_usuario = Usuario(
                nome = nome,
                cpf = cpf,
                email = email,
                papel = "usuario",
            )
            novo_usuario.set_password(senha)
            db_session.add(novo_usuario)
            db_session.flush()
            registrar_evento(
                novo_usuario.id,
                "usuarios",
                "criacao",
                novo_usuario.nome,
                novo_usuario.id,
                [
                    ("Nome", "-", novo_usuario.nome),
                    ("Perfil", "-", "Funcionário"),
                ],
            )
            db_session.commit()
            flash("Usuário criado com sucesso", "success")
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.exception("Erro ao registrar usuário")
            flash("Erro ao criar a conta. Tente novamente.", "error")
            return redirect(url_for("registro"))

    return render_template("login.html", registro=request.args.get("registro") == "True")


@app.route('/equipamentos')
@roles_required("admin", "tecnico")
def equipamentos():
    termo = request.args.get("q", "").strip()[:100]
    consulta = select(Equipamento).where(Equipamento.status_delete.is_(True))
    if termo:
        filtros = [
            Equipamento.nome.icontains(termo, autoescape=True),
            Equipamento.modelo.icontains(termo, autoescape=True),
        ]
        if termo.isdecimal() and len(termo) <= 10:
            filtros.append(Equipamento.id == int(termo))
        consulta = consulta.where(or_(*filtros))
    lista_equipamentos = db_session.execute(consulta).scalars().all()
    return render_template('equipamento.html', equipamentos=lista_equipamentos, termo=termo)


@app.route('/equipamentos/excluidos')
@roles_required("admin", "tecnico")
def listar_equipamentos_excluidos():
    termo = request.args.get("q", "").strip()[:100]
    consulta = select(Equipamento).where(Equipamento.status_delete == False)
    if termo:
        filtros = [
            Equipamento.nome.icontains(termo, autoescape=True),
            Equipamento.modelo.icontains(termo, autoescape=True),
        ]
        if termo.isdecimal() and len(termo) <= 10:
            filtros.append(Equipamento.id == int(termo))
        consulta = consulta.where(or_(*filtros))
    lista_equipamentos = db_session.execute(consulta).scalars().all()
    return render_template('equipamento.html', equipamentos=lista_equipamentos, excluidos=1, termo=termo)


@app.route('/equipamentos/cadastro', methods=['GET', 'POST'])
@roles_required("admin", "tecnico")
def cadastro_equipamento():
    if request.method == "POST":
        nome = request.form.get("nome_equipamento", "").strip()
        quantidade = request.form.get("quantidade_estoque", "").strip()
        modelo = request.form.get("modelo", "").strip()
        custo = request.form.get("custo_equipamento", "").strip()

        if tabela_equipamento.validar_equipamento(nome, quantidade, modelo, custo) is True:
            return redirect(url_for("cadastro_equipamento"))

        if tabela_equipamento.salvar(
            nome, modelo, quantidade, custo, usuario_id=current_user.id
        ):
            return redirect(url_for("equipamentos"))

    lista_equipamentos = tabela_equipamento.select_todos()
    return render_template('equipamento.html', equipamentos=lista_equipamentos)


@app.route('/equipamentos/editar/<int:equipamento_id>', methods=['GET', 'POST'])
@roles_required("admin", "tecnico")
def editar_equipamento(equipamento_id):
    equipamento = tabela_equipamento.select_id(equipamento_id)
    if not equipamento or not equipamento.status_delete:
        flash("Equipamento não encontrado", "error")
        return redirect(url_for("equipamentos"))

    if request.method == "POST":
        nome = request.form.get("nome_equipamento", "").strip()
        quantidade = request.form.get("quantidade_estoque", "").strip()
        modelo = request.form.get("modelo", "").strip()
        custo = request.form.get("custo_equipamento", "").strip()

        if tabela_equipamento.validar_equipamento(nome, quantidade, modelo, custo):
            return redirect(url_for("editar_equipamento", equipamento_id=equipamento.id))

        estado_anterior = {
            "Nome": equipamento.nome,
            "Modelo": equipamento.modelo,
            "Quantidade em estoque": equipamento.quantidade,
            "Custo unitário": equipamento.custo_equipamento,
        }
        equipamento.nome = nome
        equipamento.quantidade = int(quantidade)
        equipamento.modelo = modelo
        equipamento.custo_equipamento = float(custo)
        registrar_evento(
            current_user.id,
            "equipamentos",
            "edicao",
            equipamento.nome,
            equipamento.id,
            [
                ("Nome", estado_anterior["Nome"], equipamento.nome),
                ("Modelo", estado_anterior["Modelo"], equipamento.modelo),
                (
                    "Quantidade em estoque",
                    estado_anterior["Quantidade em estoque"],
                    equipamento.quantidade,
                ),
                (
                    "Custo unitário",
                    estado_anterior["Custo unitário"],
                    equipamento.custo_equipamento,
                ),
            ],
        )
        db_session.commit()
        flash("Equipamento atualizado com sucesso", "success")
        return redirect(url_for("equipamentos"))

    return render_template("equipamento.html", equipamentos=[], editar=equipamento)


@app.route('/equipamentos/excluir/<int:equipamento_id>', methods=['GET', 'POST'])
@roles_required("admin", "tecnico")
def excluir_equipamento(equipamento_id):
    equipamento = tabela_equipamento.select_id(equipamento_id)
    if equipamento and equipamento.status_delete:
        equipamento.status_delete = False
        registrar_evento(
            current_user.id,
            "equipamentos",
            "exclusao",
            equipamento.nome,
            equipamento.id,
            [("Status", "Ativo", "Excluído")],
        )
        db_session.commit()
    return redirect(url_for("equipamentos"))


@app.route('/equipamentos/restaurar/<int:equipamento_id>', methods=['GET', 'POST'])
@roles_required("admin", "tecnico")
def restaurar_equipamento(equipamento_id):
    equipamento = tabela_equipamento.select_id(equipamento_id)
    if equipamento and not equipamento.status_delete:
        equipamento.status_delete = True
        registrar_evento(
            current_user.id,
            "equipamentos",
            "restauracao",
            equipamento.nome,
            equipamento.id,
            [("Status", "Excluído", "Ativo")],
        )
        db_session.commit()
    return redirect(url_for("listar_equipamentos_excluidos"))


@app.route('/ordens_servico', methods=['GET'])
@login_required
def ordens_servico_lista_view():
    return listar_ordens_servico(excluidos=False)


@app.route('/ordens_servico/excluidos', methods=['GET'])
@login_required
def listar_ordens_servico_excluidos():
    return listar_ordens_servico(excluidos=True)


def restringir_ordens_por_perfil(consulta):
    if current_user.papel == "admin":
        return consulta
    if current_user.papel == "tecnico":
        return consulta.where(
            OrdemServico.tecnico_responsavel_id == current_user.id
        )
    if current_user.papel == "usuario":
        return consulta.where(OrdemServico.responsavel_id == current_user.id)
    return consulta.where(OrdemServico.id == -1)


def listar_ordens_servico(excluidos):
    termo = request.args.get("q", "").strip()[:100]
    consulta = restringir_ordens_por_perfil(
        select(OrdemServico).where(OrdemServico.status_delete.is_(not excluidos))
    )
    if termo:
        filtros = [
            OrdemServico.descricao.icontains(termo, autoescape=True),
            OrdemServico.status_os.icontains(termo, autoescape=True),
            OrdemServico.prioridade.icontains(termo, autoescape=True),
            OrdemServico.categoria.icontains(termo, autoescape=True),
            Usuario.nome.icontains(termo, autoescape=True),
            OrdemServico.tecnico_responsavel.has(
                Usuario.nome.icontains(termo, autoescape=True)
            ),
            OrdemServico.setor.has(Setor.nome.icontains(termo, autoescape=True)),
            OrdemServico.equipamentos_associados.any(
                OrdemServicoEquipamento.equipamento.has(
                    Equipamento.nome.icontains(termo, autoescape=True)
                )
            ),
        ]
        if termo.isdecimal() and len(termo) <= 10:
            filtros.append(OrdemServico.id == int(termo))
        consulta = consulta.outerjoin(
            Usuario, OrdemServico.responsavel_id == Usuario.id
        ).where(or_(*filtros))
    lista_ordens = db_session.execute(consulta.order_by(OrdemServico.id.asc())).scalars().all()
    exclusoes_por_os = {}
    solicitacoes_por_os = {}
    if excluidos and lista_ordens:
        ordem_ids = [ordem.id for ordem in lista_ordens]
        exclusoes = db_session.execute(
            select(AuditoriaSistema)
            .where(
                AuditoriaSistema.area == "ordens_servico",
                AuditoriaSistema.acao == "exclusao",
                AuditoriaSistema.registro_id.in_(ordem_ids),
            )
            .order_by(AuditoriaSistema.id.desc())
        ).scalars().all()
        for evento in exclusoes:
            exclusoes_por_os.setdefault(evento.registro_id, evento)

        if current_user.papel != "admin":
            solicitacoes = db_session.execute(
                select(SolicitacaoRestauracaoOS)
                .where(
                    SolicitacaoRestauracaoOS.ordem_servico_id.in_(ordem_ids),
                    SolicitacaoRestauracaoOS.usuario_id == current_user.id,
                )
                .order_by(SolicitacaoRestauracaoOS.id.desc())
            ).scalars().all()
            for solicitacao in solicitacoes:
                solicitacoes_por_os.setdefault(
                    solicitacao.ordem_servico_id, solicitacao
                )

    return render_template(
        'ordens_servico.html',
        ordens=lista_ordens,
        termo=termo,
        excluidos=excluidos,
        exclusoes_por_os=exclusoes_por_os,
        solicitacoes_por_os=solicitacoes_por_os,
    )


@app.route('/servico/ordens/cadastro', methods=['GET', 'POST'])
@roles_required("admin", "usuario")
def cadastro_ordem_view():
    if request.method == "POST":
        funcionario = current_user.papel == "usuario"
        responsavel_id = (
            current_user.id if funcionario else request.form.get("responsavel_id")
        )
        tecnico_responsavel_id = (
            request.form.get("tecnico_responsavel_id")
            if current_user.papel in {"admin", "usuario"}
            else None
        )
        descricao = request.form.get("descricao", "").strip()
        categoria = request.form.get("categoria", "")
        setor_id = request.form.get("setor_id", "")
        equipamentos_ids = [] if funcionario else request.form.getlist("equipamentos_ids")
        status_os = "Aberta" if funcionario else request.form.get("status_os")
        prioridade = "Média" if funcionario else request.form.get("prioridade")
        custo_total = 0 if funcionario else request.form.get("custo_total")
        data_solicitacao = request.form.get("data_solicitacao")
        data_execucao = None

        identificacao = tabela_ordens_servico.gerar_identificacao(current_user.nome)

        if tabela_ordens_servico.salvar(
            0,
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
            permitir_sem_equipamentos=funcionario,
            usuario_id=current_user.id,
        ):
            return redirect(url_for("ordens_servico_lista_view"))

    usuarios_comuns = tabela_usuario.select_comuns()
    lista_ordens = tabela_ordens_servico.select_todas()
    return render_template(
        'ordens_servico.html',
        usuarios=usuarios_comuns,
        ordens=lista_ordens,
        categorias_os=tabela_ordens_servico.CATEGORIAS_OS,
        setores=tabela_setor.select_ativos(),
        equipamentos=tabela_equipamento.select_ativos(),
        tecnicos=tabela_usuario.select_tecnicos_para_atribuicao(),
        equipamentos_selecionados=[],
    )


@app.route('/servico/ordens/<int:ordem_id>')
@login_required
def detalhes_ordem_servico(ordem_id):
    consulta = restringir_ordens_por_perfil(
        select(OrdemServico)
        .where(
            OrdemServico.id == ordem_id,
            OrdemServico.status_delete.is_(True),
        )
    )
    ordem_servico = db_session.execute(consulta).scalar_one_or_none()
    if not ordem_servico:
        flash("Ordem de serviço não encontrada", "error")
        return redirect(url_for("ordens_servico_lista_view"))

    historico = db_session.execute(
        select(HistoricoOrdemServico)
        .where(HistoricoOrdemServico.ordem_servico_id == ordem_id)
        .order_by(
            HistoricoOrdemServico.criado_em.desc(),
            HistoricoOrdemServico.id.desc(),
        )
    ).scalars().all()
    total_mensagens = db_session.execute(
        select(func.count(MensagemOrdemServico.id)).where(
            MensagemOrdemServico.ordem_servico_id == ordem_id
        )
    ).scalar_one()
    return render_template(
        "ordem_servico_detalhes.html",
        ordem=ordem_servico,
        historico=historico,
        total_mensagens=total_mensagens,
    )


@app.route('/servico/ordens/<int:ordem_id>/conversa')
@login_required
def conversa_ordem_servico(ordem_id):
    consulta = restringir_ordens_por_perfil(
        select(OrdemServico).where(
            OrdemServico.id == ordem_id,
            OrdemServico.status_delete.is_(True),
        )
    )
    ordem_servico = db_session.execute(consulta).scalar_one_or_none()
    if not ordem_servico:
        flash("Ordem de serviço não encontrada.", "error")
        return redirect(url_for("ordens_servico_lista_view"))

    mensagens = db_session.execute(
        select(MensagemOrdemServico)
        .where(MensagemOrdemServico.ordem_servico_id == ordem_id)
        .order_by(
            MensagemOrdemServico.criado_em.asc(),
            MensagemOrdemServico.id.asc(),
        )
    ).scalars().all()
    return render_template(
        "conversa_ordem_servico.html",
        ordem=ordem_servico,
        mensagens=mensagens,
    )


@app.route('/servico/ordens/<int:ordem_id>/mensagens', methods=['POST'])
@login_required
def enviar_mensagem_ordem_servico(ordem_id):
    consulta = restringir_ordens_por_perfil(
        select(OrdemServico).where(
            OrdemServico.id == ordem_id,
            OrdemServico.status_delete.is_(True),
        )
    )
    ordem_servico = db_session.execute(consulta).scalar_one_or_none()
    if not ordem_servico:
        flash("Ordem de serviço não encontrada.", "error")
        return redirect(url_for("ordens_servico_lista_view"))

    mensagem = request.form.get("mensagem", "").strip()
    if not mensagem:
        flash("Digite uma mensagem antes de enviar.", "error")
        return redirect(url_for("conversa_ordem_servico", ordem_id=ordem_id))
    if len(mensagem) > 2000:
        flash("A mensagem pode ter no máximo 2.000 caracteres.", "error")
        return redirect(url_for("conversa_ordem_servico", ordem_id=ordem_id))

    db_session.add(
        MensagemOrdemServico(
            ordem_servico_id=ordem_id,
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            usuario_papel=current_user.papel,
            mensagem=mensagem,
        )
    )
    try:
        db_session.commit()
        flash("Mensagem enviada.", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception(
            "Erro ao enviar mensagem para a ordem de serviço %s", ordem_id
        )
        flash("Não foi possível enviar a mensagem. Tente novamente.", "error")
    return redirect(url_for("conversa_ordem_servico", ordem_id=ordem_id))


@app.route('/servico/ordens/excluir/<int:ordem_id>', methods=['POST'])
@roles_required("admin")
def excluir_ordem_servico(ordem_id):
    ordem_servico = tabela_ordens_servico.select_ordem_id(ordem_id)
    if not ordem_servico or not ordem_servico.status_delete:
        flash("Ordem de serviço não encontrada", "error")
        return redirect(url_for("ordens_servico_lista_view"))

    ordem_servico.status_delete = False
    try:
        registrar_evento(
            current_user.id,
            "ordens_servico",
            "exclusao",
            f"OS #{ordem_servico.id}",
            ordem_servico.id,
            [("Status", "Ativa", "Excluída")],
        )
        db_session.add(
            HistoricoOrdemServico(
                ordem_servico_id=ordem_id,
                usuario_id=current_user.id,
                campo="Registro da OS",
                valor_anterior="Ativa",
                valor_novo="Excluída",
            )
        )
        db_session.commit()
        flash("Ordem de serviço excluída com sucesso", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception("Erro ao excluir ordem de serviço %s", ordem_id)
        flash("Erro ao excluir a ordem de serviço", "error")
    return redirect(url_for("ordens_servico_lista_view"))


@app.route('/servico/ordens/restaurar/<int:ordem_id>', methods=['POST'])
@roles_required("admin")
def restaurar_ordem_servico(ordem_id):
    ordem_servico = tabela_ordens_servico.select_ordem_id(ordem_id)
    if not ordem_servico or ordem_servico.status_delete:
        flash("Ordem de serviço excluída não encontrada", "error")
        return redirect(url_for("listar_ordens_servico_excluidos"))

    ordem_servico.status_delete = True
    try:
        registrar_evento(
            current_user.id,
            "ordens_servico",
            "restauracao",
            f"OS #{ordem_servico.id}",
            ordem_servico.id,
            [("Status", "Excluída", "Ativa")],
        )
        db_session.add(
            HistoricoOrdemServico(
                ordem_servico_id=ordem_id,
                usuario_id=current_user.id,
                campo="Registro da OS",
                valor_anterior="Excluída",
                valor_novo="Ativa",
            )
        )
        solicitacoes_pendentes = db_session.execute(
            select(SolicitacaoRestauracaoOS).where(
                SolicitacaoRestauracaoOS.ordem_servico_id == ordem_id,
                SolicitacaoRestauracaoOS.status == "pendente",
            )
        ).scalars().all()
        for solicitacao in solicitacoes_pendentes:
            solicitacao.status = "restaurada"
            solicitacao.resposta_administrador = "A ordem de serviço foi restaurada."
            solicitacao.administrador_id = current_user.id
            solicitacao.resolvido_em = datetime.now()
        db_session.commit()
        flash("Ordem de serviço restaurada com sucesso", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception("Erro ao restaurar ordem de serviço %s", ordem_id)
        flash("Erro ao restaurar a ordem de serviço", "error")
    return redirect(url_for("listar_ordens_servico_excluidos"))


@app.route('/servico/ordens/<int:ordem_id>/solicitar-restauracao', methods=['POST'])
@login_required
def solicitar_restauracao_ordem_servico(ordem_id):
    if current_user.papel not in {"usuario", "tecnico"}:
        flash("Somente funcionários e técnicos podem solicitar a restauração.", "error")
        return redirect(url_for("listar_ordens_servico_excluidos"))

    consulta = restringir_ordens_por_perfil(
        select(OrdemServico).where(
            OrdemServico.id == ordem_id,
            OrdemServico.status_delete.is_(False),
        )
    )
    ordem_servico = db_session.execute(consulta).scalar_one_or_none()
    if not ordem_servico:
        flash("Ordem de serviço excluída não encontrada.", "error")
        return redirect(url_for("listar_ordens_servico_excluidos"))

    pendente = db_session.execute(
        select(SolicitacaoRestauracaoOS.id).where(
            SolicitacaoRestauracaoOS.ordem_servico_id == ordem_id,
            SolicitacaoRestauracaoOS.usuario_id == current_user.id,
            SolicitacaoRestauracaoOS.status == "pendente",
        )
    ).scalar_one_or_none()
    if pendente:
        flash("Você já tem uma solicitação pendente para esta ordem de serviço.", "error")
        return redirect(url_for("listar_ordens_servico_excluidos"))

    mensagem = request.form.get("mensagem", "").strip()
    if not mensagem or len(mensagem) > 500:
        flash("Informe uma justificativa de até 500 caracteres.", "error")
        return redirect(url_for("listar_ordens_servico_excluidos"))

    db_session.add(
        SolicitacaoRestauracaoOS(
            ordem_servico_id=ordem_id,
            usuario_id=current_user.id,
            usuario_nome=current_user.nome,
            usuario_papel=current_user.papel,
            mensagem=mensagem,
        )
    )
    try:
        db_session.commit()
        flash("Solicitação enviada ao administrador.", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception(
            "Erro ao solicitar restauração da ordem de serviço %s", ordem_id
        )
        flash("Não foi possível enviar a solicitação. Tente novamente.", "error")
    return redirect(url_for("listar_ordens_servico_excluidos"))


@app.route('/solicitacoes-restauracao')
@roles_required("admin")
def listar_solicitacoes_restauracao():
    solicitacoes = db_session.execute(
        select(SolicitacaoRestauracaoOS)
        .order_by(
            (SolicitacaoRestauracaoOS.status == "pendente").desc(),
            SolicitacaoRestauracaoOS.criado_em.desc(),
            SolicitacaoRestauracaoOS.id.desc(),
        )
    ).scalars().all()
    return render_template(
        "solicitacoes_restauracao.html",
        solicitacoes=solicitacoes,
    )


@app.route(
    '/solicitacoes-restauracao/<int:solicitacao_id>/recusar',
    methods=['POST'],
)
@roles_required("admin")
def recusar_solicitacao_restauracao(solicitacao_id):
    solicitacao = db_session.get(SolicitacaoRestauracaoOS, solicitacao_id)
    if not solicitacao or solicitacao.status != "pendente":
        flash("Solicitação pendente não encontrada.", "error")
        return redirect(url_for("listar_solicitacoes_restauracao"))

    resposta = request.form.get("resposta", "").strip()
    if len(resposta) > 500:
        flash("A resposta pode ter no máximo 500 caracteres.", "error")
        return redirect(url_for("listar_solicitacoes_restauracao"))

    solicitacao.status = "recusada"
    solicitacao.resposta_administrador = resposta or "Solicitação recusada."
    solicitacao.administrador_id = current_user.id
    solicitacao.resolvido_em = datetime.now()
    try:
        db_session.commit()
        flash("Solicitação recusada.", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception(
            "Erro ao recusar solicitação de restauração %s", solicitacao_id
        )
        flash("Não foi possível recusar a solicitação.", "error")
    return redirect(url_for("listar_solicitacoes_restauracao"))


@app.route('/servico/ordens/editar/<int:ordem_id>', methods=['GET', 'POST'])
@roles_required("admin", "tecnico")
def editar_ordem_servico(ordem_id):
    ordem_servico = tabela_ordens_servico.select_ordem_id(ordem_id)
    if (
        not ordem_servico
        or (
            current_user.papel == "tecnico"
            and not ordem_servico.status_delete
        )
        or (
            current_user.papel == "tecnico"
            and ordem_servico.tecnico_responsavel_id != current_user.id
        )
    ):
        flash("Ordem de serviço não encontrada", "error")
        return redirect(url_for("ordens_servico_lista_view"))

    if request.method == "POST":
        if current_user.papel == "tecnico":
            status_os = request.form.get("status_os", "")
            prioridade = request.form.get("prioridade", "")
            data_execucao_str = request.form.get("data_execucao", "").strip()
            if data_execucao_str:
                try:
                    data_execucao = datetime.strptime(
                        data_execucao_str, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    flash("Informe uma data de execução válida", "error")
                    return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))
            else:
                data_execucao = None

            if (
                ordem_servico.data_solicitacao
                and data_execucao
                and data_execucao < ordem_servico.data_solicitacao
            ):
                flash("A data de execução não pode ser anterior à solicitação", "error")
                return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

            try:
                custo_total = int(request.form.get("custo_total") or 0)
            except ValueError:
                flash("Informe um custo estimado válido", "error")
                return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

            if custo_total < 0:
                flash("O custo estimado não pode ser negativo", "error")
                return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))
            if status_os not in tabela_ordens_servico.STATUS_OS:
                flash("Selecione um status válido", "error")
                return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))
            if prioridade not in {"Baixa", "Média", "Alta"}:
                flash("Selecione uma prioridade válida", "error")
                return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

            equipamentos_atuais = {
                associacao.equipamento_id
                for associacao in ordem_servico.equipamentos_associados
            }
            equipamentos_ids = list(equipamentos_atuais) + request.form.getlist(
                "equipamentos_ids"
            )
            equipamentos_ids = tabela_ordens_servico.validar_equipamentos(
                equipamentos_ids,
                equipamentos_atuais,
            )
            if equipamentos_ids is None:
                return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

            estado_anterior = tabela_ordens_servico.capturar_estado_historico(
                ordem_servico,
                equipamentos_atuais,
            )
            ordem_servico.status_os = status_os
            ordem_servico.prioridade = prioridade
            ordem_servico.custo_total = custo_total
            ordem_servico.data_execucao = data_execucao
            try:
                novos_equipamentos = set(equipamentos_ids) - equipamentos_atuais
                db_session.add_all(
                    OrdemServicoEquipamento(
                        os_id=ordem_servico.id,
                        equipamento_id=equipamento_id,
                        quantidade=1,
                    )
                    for equipamento_id in novos_equipamentos
                )
                db_session.flush()
                estado_novo = tabela_ordens_servico.capturar_estado_historico(
                    ordem_servico,
                    equipamentos_ids,
                )
                tabela_ordens_servico.registrar_historico(
                    ordem_servico.id,
                    current_user.id,
                    estado_anterior,
                    estado_novo,
                )
                db_session.commit()
                flash("Ordem de serviço atualizada com sucesso", "success")
                return redirect(url_for("detalhes_ordem_servico", ordem_id=ordem_id))
            except SQLAlchemyError:
                db_session.rollback()
                app.logger.exception(
                    "Erro ao atualizar ordem de serviço %s como técnico", ordem_id
                )
                flash("Erro ao atualizar a ordem de serviço", "error")
                return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

        responsavel_id = request.form.get("responsavel_id")
        tecnico_responsavel_id = (
            request.form.get("tecnico_responsavel_id")
            if current_user.papel in {"admin", "usuario"}
            else ordem_servico.tecnico_responsavel_id
        )
        descricao = request.form.get("descricao", "").strip()
        categoria = request.form.get("categoria", "")
        setor_id = request.form.get("setor_id", "")
        equipamentos_ids = request.form.getlist("equipamentos_ids")
        status_os = request.form.get("status_os")
        prioridade = request.form.get("prioridade")
        custo_total = request.form.get("custo_total")
        data_execucao = ordem_servico.data_execucao

        if not descricao:
            flash("Preencha a descrição da ordem de serviço", "error")
            return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))
        if status_os not in tabela_ordens_servico.STATUS_OS:
            flash("Selecione um status válido", "error")
            return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

        try:
            responsavel_id = int(responsavel_id) if responsavel_id else None
            custo_total = int(custo_total) if custo_total else 0
        except ValueError:
            flash("Funcionário ou custo inválido", "error")
            return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

        if custo_total < 0:
            flash("O custo estimado não pode ser negativo", "error")
            return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

        vinculos = tabela_ordens_servico.validar_vinculos(
            categoria,
            setor_id,
            equipamentos_ids,
            ordem_atual=ordem_servico,
        )
        if vinculos is None:
            return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))
        setor_id, equipamentos_ids = vinculos
        tecnico_responsavel_id = tabela_ordens_servico.validar_tecnico(
            tecnico_responsavel_id,
            tecnico_atual_id=ordem_servico.tecnico_responsavel_id,
        )
        if tecnico_responsavel_id is False:
            return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

        equipamentos_anteriores_ids = [
            associacao.equipamento_id
            for associacao in ordem_servico.equipamentos_associados
        ]
        estado_anterior = tabela_ordens_servico.capturar_estado_historico(
            ordem_servico,
            equipamentos_anteriores_ids,
        )
        ordem_servico.responsavel_id = responsavel_id
        ordem_servico.tecnico_responsavel_id = tecnico_responsavel_id
        ordem_servico.categoria = categoria
        ordem_servico.setor_id = setor_id
        ordem_servico.descricao = descricao
        ordem_servico.status_os = status_os
        ordem_servico.prioridade = prioridade
        ordem_servico.custo_total = custo_total
        ordem_servico.data_execucao = data_execucao

        try:
            associacoes_anteriores = list(ordem_servico.equipamentos_associados)
            quantidades_anteriores = {
                associacao.equipamento_id: associacao.quantidade
                for associacao in associacoes_anteriores
            }
            for associacao in associacoes_anteriores:
                db_session.delete(associacao)
            db_session.flush()
            db_session.add_all(
                OrdemServicoEquipamento(
                    os_id=ordem_servico.id,
                    equipamento_id=equipamento_id,
                    quantidade=quantidades_anteriores.get(equipamento_id, 1),
                )
                for equipamento_id in equipamentos_ids
            )
            db_session.flush()
            estado_novo = tabela_ordens_servico.capturar_estado_historico(
                ordem_servico,
                equipamentos_ids,
            )
            tabela_ordens_servico.registrar_historico(
                ordem_servico.id,
                current_user.id,
                estado_anterior,
                estado_novo,
            )
            db_session.commit()
            flash("Ordem de Serviço editada com sucesso", "success")
            return redirect(url_for("ordens_servico_lista_view"))
        except SQLAlchemyError:
            db_session.rollback()
            flash("Erro ao editar a ordem de serviço", "error")
            return redirect(url_for("editar_ordem_servico", ordem_id=ordem_id))

    usuarios_comuns = tabela_usuario.select_comuns_para_atribuicao(
        ordem_servico.responsavel_id
    )
    tecnicos = tabela_usuario.select_tecnicos_para_atribuicao(
        ordem_servico.tecnico_responsavel_id
    )
    setores_disponiveis = tabela_setor.select_ativos()
    if ordem_servico.setor and ordem_servico.setor not in setores_disponiveis:
        setores_disponiveis.append(ordem_servico.setor)
    equipamentos_disponiveis = tabela_equipamento.select_ativos()
    for associacao in ordem_servico.equipamentos_associados:
        if associacao.equipamento and associacao.equipamento not in equipamentos_disponiveis:
            equipamentos_disponiveis.append(associacao.equipamento)
    return render_template(
        'ordens_servico.html',
        editar=ordem_servico,
        usuarios=usuarios_comuns,
        categorias_os=tabela_ordens_servico.CATEGORIAS_OS,
        setores=setores_disponiveis,
        equipamentos=equipamentos_disponiveis,
        tecnicos=tecnicos,
        equipamentos_selecionados=[
            associacao.equipamento_id
            for associacao in ordem_servico.equipamentos_associados
        ],
    )

@app.route('/setor', methods=['GET'])
@roles_required("admin")
def setor():
    termo = request.args.get("q", "").strip()[:100]
    lista_setores = consultar_setores(True, termo)
    return render_template('setor.html', setores=lista_setores, termo=termo)


@app.route('/setor/excluidos', methods=['GET'])
@roles_required("admin")
def listar_setores_excluidos():
    termo = request.args.get("q", "").strip()[:100]
    lista_setores = consultar_setores(False, termo)
    return render_template('setor.html', setores=lista_setores, excluidos=1, termo=termo)


def consultar_setores(ativos, termo):
    consulta = select(Setor).where(Setor.status_delete == ativos)
    if termo:
        filtros = [
            Setor.nome.icontains(termo, autoescape=True),
            Setor.descricao.icontains(termo, autoescape=True),
        ]
        if termo.isdecimal() and len(termo) <= 10:
            filtros.append(Setor.id == int(termo))
        consulta = consulta.where(or_(*filtros))
    return db_session.execute(consulta.order_by(Setor.id.asc())).scalars().all()


@app.route('/setor/cadastro', methods=['GET', 'POST'])
@roles_required("admin")
def cadastro_setor():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if tabela_setor.validar_setor(nome, descricao):
            return redirect(url_for("cadastro_setor"))

        if tabela_setor.salvar(nome, descricao, usuario_id=current_user.id):
            return redirect(url_for("setor"))

    lista_setores = tabela_setor.select_todos()
    return render_template('setor.html', setores=lista_setores)


@app.route('/setor/editar/<int:setor_id>', methods=['GET', 'POST'])
@roles_required("admin")
def editar_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if not setor:
        flash("Setor não encontrado", "error")
        return redirect(url_for("setor"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if tabela_setor.validar_setor(nome, descricao):
            return redirect(url_for("editar_setor", setor_id=setor.id))

        nome_anterior = setor.nome
        descricao_anterior = setor.descricao
        setor.nome = nome
        setor.descricao = descricao
        registrar_evento(
            current_user.id,
            "setores",
            "edicao",
            setor.nome,
            setor.id,
            [
                ("Nome", nome_anterior, setor.nome),
                ("Descrição", descricao_anterior, setor.descricao),
            ],
        )
        db_session.commit()
        flash("Setor atualizado com sucesso", "success")
        return redirect(url_for("setor"))

    return render_template("setor.html", setores=[], editar=setor)


@app.route('/setor/excluir/<setor_id>', methods=['GET', 'POST'])
@roles_required("admin")
def excluir_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if setor and setor.status_delete:
        setor.status_delete = False
        registrar_evento(
            current_user.id,
            "setores",
            "exclusao",
            setor.nome,
            setor.id,
            [("Status", "Ativo", "Excluído")],
        )
        db_session.commit()
    return redirect(url_for('setor'))


@app.route('/setor/restaurar/<setor_id>', methods=['GET', 'POST'])
@roles_required("admin")
def restaurar_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if setor and not setor.status_delete:
        setor.status_delete = True
        registrar_evento(
            current_user.id,
            "setores",
            "restauracao",
            setor.nome,
            setor.id,
            [("Status", "Excluído", "Ativo")],
        )
        db_session.commit()
    return redirect(url_for('listar_setores_excluidos'))


@app.route('/funcionarios', methods=['GET'])
@roles_required("admin")
def funcionarios():
    termo = request.args.get("q", "").strip()[:100]
    consulta = select(Usuario).where(Usuario.papel.in_(("usuario", "tecnico")))
    if termo:
        filtros = [
            Usuario.nome.icontains(termo, autoescape=True),
            Usuario.email.icontains(termo, autoescape=True),
            Usuario.funcao.icontains(termo, autoescape=True),
            cast(Usuario.cpf, String).contains(termo, autoescape=True),
            Setor.nome.icontains(termo, autoescape=True),
        ]
        if termo.isdecimal() and len(termo) <= 10:
            filtros.append(Usuario.id == int(termo))
        consulta = consulta.outerjoin(Setor, Usuario.setor_id == Setor.id).where(or_(*filtros))
    lista_usuarios = db_session.execute(consulta.order_by(Usuario.id.asc())).scalars().all()
    return render_template('funcionario.html', usuarios=lista_usuarios, termo=termo)

@app.route('/funcionarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@roles_required("admin")
def editar_funcionario(usuario_id):
    usuario = db_session.get(Usuario, usuario_id)
    if not usuario or usuario.papel not in {"usuario", "tecnico"}:
        flash("Funcionário não encontrado", "error")
        return redirect(url_for("funcionarios"))

    setores = tabela_setor.select_ativos()
    if request.method == "POST":
        setor_id = request.form.get("setor")
        funcao = request.form.get("funcao", "").strip()
        papel = request.form.get("papel", "")

        try:
            setor_id = int(setor_id)
        except (TypeError, ValueError):
            flash("Selecione um setor válido", "error")
            return redirect(url_for("editar_funcionario", usuario_id=usuario.id))

        setor = db_session.execute(
            select(Setor).where(Setor.id == setor_id, Setor.status_delete.is_(True))
        ).scalar_one_or_none()
        if not setor:
            flash("O setor selecionado não está disponível", "error")
            return redirect(url_for("editar_funcionario", usuario_id=usuario.id))
        if not funcao:
            flash("Preencha a função ou cargo", "error")
            return redirect(url_for("editar_funcionario", usuario_id=usuario.id))
        if len(funcao) > 100:
            flash("A função ou cargo pode ter no máximo 100 caracteres", "error")
            return redirect(url_for("editar_funcionario", usuario_id=usuario.id))
        if papel not in {"usuario", "tecnico"}:
            flash("Selecione um perfil válido", "error")
            return redirect(url_for("editar_funcionario", usuario_id=usuario.id))

        setor_anterior = usuario.setor.nome if usuario.setor else "Não atribuído"
        funcao_anterior = usuario.funcao or "Não atribuída"
        papel_anterior = (
            "Técnico" if usuario.papel == "tecnico" else "Funcionário"
        )
        usuario.setor = setor
        usuario.funcao = funcao
        usuario.papel = papel
        try:
            registrar_evento(
                current_user.id,
                "usuarios",
                "edicao",
                usuario.nome,
                usuario.id,
                [
                    ("Setor", setor_anterior, setor.nome),
                    ("Função/cargo", funcao_anterior, funcao),
                    (
                        "Perfil",
                        papel_anterior,
                        "Técnico" if papel == "tecnico" else "Funcionário",
                    ),
                ],
            )
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            app.logger.exception("Erro ao atualizar funcionário %s", usuario.id)
            flash("Erro ao atualizar os dados do funcionário", "error")
            return redirect(url_for("editar_funcionario", usuario_id=usuario.id))

        flash("Dados do funcionário atualizados com sucesso", "success")
        return redirect(url_for("funcionarios"))

    return render_template("funcionario.html", editar=usuario, setores=setores)


@app.route('/funcionarios/<int:usuario_id>/inativar', methods=['POST'])
@roles_required("admin")
def inativar_funcionario(usuario_id):
    usuario = db_session.get(Usuario, usuario_id)
    if not usuario or usuario.papel not in {"usuario", "tecnico"}:
        flash("Funcionário não encontrado", "error")
        return redirect(url_for("funcionarios"))

    estava_ativo = usuario.ativo
    usuario.ativo = False
    try:
        if estava_ativo:
            registrar_evento(
                current_user.id,
                "usuarios",
                "inativacao",
                usuario.nome,
                usuario.id,
                [("Status", "Ativo", "Inativo")],
            )
        db_session.commit()
        flash("Funcionário inativado com sucesso. As OS atuais foram mantidas.", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception("Erro ao inativar funcionário %s", usuario_id)
        flash("Erro ao inativar o funcionário", "error")
    return redirect(url_for("funcionarios"))


@app.route('/funcionarios/<int:usuario_id>/ativar', methods=['POST'])
@roles_required("admin")
def ativar_funcionario(usuario_id):
    usuario = db_session.get(Usuario, usuario_id)
    if not usuario or usuario.papel not in {"usuario", "tecnico"}:
        flash("Funcionário não encontrado", "error")
        return redirect(url_for("funcionarios"))

    estava_ativo = usuario.ativo
    usuario.ativo = True
    try:
        if not estava_ativo:
            registrar_evento(
                current_user.id,
                "usuarios",
                "ativacao",
                usuario.nome,
                usuario.id,
                [("Status", "Inativo", "Ativo")],
            )
        db_session.commit()
        flash("Funcionário ativado com sucesso", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception("Erro ao ativar funcionário %s", usuario_id)
        flash("Erro ao ativar o funcionário", "error")
    return redirect(url_for("funcionarios"))


@app.route('/auditoria')
@roles_required("admin")
def auditoria_sistema():
    areas = (
        ("ordens_servico", "Ordens de serviço"),
        ("equipamentos", "Equipamentos/estoque"),
        ("usuarios", "Usuários"),
        ("setores", "Setores"),
    )
    acoes = (
        ("criacao", "Criação"),
        ("edicao", "Edição"),
        ("exclusao", "Exclusão"),
        ("restauracao", "Restauração"),
        ("ativacao", "Ativação"),
        ("inativacao", "Inativação"),
    )
    filtros = {
        "inicio": request.args.get("inicio", "").strip(),
        "fim": request.args.get("fim", "").strip(),
        "area": request.args.get("area", "").strip(),
        "acao": request.args.get("acao", "").strip(),
        "usuario": request.args.get("usuario", "").strip()[:100],
    }
    consulta = select(AuditoriaSistema)

    if filtros["inicio"]:
        try:
            inicio = datetime.strptime(filtros["inicio"], "%Y-%m-%d")
        except ValueError:
            flash("Data inicial inválida", "error")
            return redirect(url_for("auditoria_sistema"))
        consulta = consulta.where(AuditoriaSistema.criado_em >= inicio)
    if filtros["fim"]:
        try:
            fim = datetime.strptime(filtros["fim"], "%Y-%m-%d")
        except ValueError:
            flash("Data final inválida", "error")
            return redirect(url_for("auditoria_sistema"))
        consulta = consulta.where(AuditoriaSistema.criado_em < fim + timedelta(days=1))
    if filtros["area"] in {codigo for codigo, _ in areas}:
        consulta = consulta.where(AuditoriaSistema.area == filtros["area"])
    if filtros["acao"] in {codigo for codigo, _ in acoes}:
        consulta = consulta.where(AuditoriaSistema.acao == filtros["acao"])
    if filtros["usuario"]:
        consulta = consulta.where(
            or_(
                AuditoriaSistema.usuario_nome.icontains(
                    filtros["usuario"], autoescape=True
                ),
                AuditoriaSistema.registro.icontains(
                    filtros["usuario"], autoescape=True
                ),
            )
        )

    total = db_session.execute(
        select(func.count()).select_from(consulta.subquery())
    ).scalar_one()
    por_pagina = 50
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
    try:
        pagina = int(request.args.get("pagina", "1"))
    except ValueError:
        pagina = 1
    pagina = min(max(pagina, 1), total_paginas)
    movimentacoes = db_session.execute(
        consulta.order_by(
            AuditoriaSistema.criado_em.desc(),
            AuditoriaSistema.id.desc(),
        )
        .limit(por_pagina)
        .offset((pagina - 1) * por_pagina)
    ).scalars().all()
    return render_template(
        "auditoria.html",
        movimentacoes=movimentacoes,
        areas=areas,
        acoes=acoes,
        filtros=filtros,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
    )


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    ordens_visiveis = restringir_ordens_por_perfil(
        select(OrdemServico)
    ).subquery()
    ordens_servico = db_session.execute(
        select(func.count()).select_from(ordens_visiveis)
    ).scalar_one()
    equipamentos = tabela_equipamento.select_quantidade_total()
    setores = tabela_setor.select_quantidade_total()
    usuarios_comuns = tabela_usuario.select_quantidade_comuns()
    ordens_status = db_session.execute(
        select(ordens_visiveis.c.status_os, func.count())
        .select_from(ordens_visiveis)
        .group_by(ordens_visiveis.c.status_os)
        .order_by(ordens_visiveis.c.status_os.asc())
    ).all()

    return render_template(
        "dashboard.html",
        total_ordens_servico=ordens_servico,
        total_equipamentos=equipamentos,
        total_setores=setores,
        total_usuarios=usuarios_comuns,
        ordens_status=ordens_status,
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
