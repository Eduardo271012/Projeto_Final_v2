from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from sqlalchemy import String, cast, or_, select
from sqlalchemy.exc import SQLAlchemyError
from banco import tabela_equipamento, tabela_ordens_servico, tabela_setor, tabela_usuario
from database import (
    Equipamento,
    OrdemServico,
    OrdemServicoEquipamento,
    Setor,
    Usuario,
    db_session,
)
from functools import wraps
from datetime import datetime
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
            flash(f"BEM-VINDO(A), {usuario_resultado.nome}!😁", "welcome")
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
            db_session.commit()
            flash("Usuário criado com sucesso", "success")
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.exception("Erro ao registrar usuário")
            flash("Erro ao criar a conta. Tente novamente.", "error")
            return redirect(url_for("registro"))

    return render_template("login.html", registro=request.args.get("registro") == "True")


@app.route('/equipamentos')
@login_required
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
@login_required
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
@login_required
def cadastro_equipamento():
    if request.method == "POST":
        nome = request.form.get("nome_equipamento", "").strip()
        quantidade = request.form.get("quantidade_estoque", "").strip()
        modelo = request.form.get("modelo", "").strip()
        custo = request.form.get("custo_equipamento", "").strip()

        if tabela_equipamento.validar_equipamento(nome, quantidade, modelo, custo) is True:
            return redirect(url_for("cadastro_equipamento"))

        if tabela_equipamento.salvar(nome, modelo, quantidade, custo):
            return redirect(url_for("equipamentos"))

    lista_equipamentos = tabela_equipamento.select_todos()
    return render_template('equipamento.html', equipamentos=lista_equipamentos)


@app.route('/equipamentos/editar/<int:equipamento_id>', methods=['GET', 'POST'])
@login_required
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

        equipamento.nome = nome
        equipamento.quantidade = int(quantidade)
        equipamento.modelo = modelo
        equipamento.custo_equipamento = float(custo)
        db_session.commit()
        flash("Equipamento atualizado com sucesso", "success")
        return redirect(url_for("equipamentos"))

    return render_template("equipamento.html", equipamentos=[], editar=equipamento)


@app.route('/equipamentos/excluir/<int:equipamento_id>', methods=['GET', 'POST'])
@login_required
def excluir_equipamento(equipamento_id):
    equipamento = tabela_equipamento.select_id(equipamento_id)
    if equipamento and equipamento.status_delete:
        equipamento.status_delete = False
        db_session.commit()
    return redirect(url_for("equipamentos"))


@app.route('/equipamentos/restaurar/<int:equipamento_id>', methods=['GET', 'POST'])
@login_required
def restaurar_equipamento(equipamento_id):
    equipamento = tabela_equipamento.select_id(equipamento_id)
    if equipamento and not equipamento.status_delete:
        equipamento.status_delete = True
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


def listar_ordens_servico(excluidos):
    termo = request.args.get("q", "").strip()[:100]
    consulta = select(OrdemServico).where(OrdemServico.status_delete.is_(not excluidos))
    if termo:
        filtros = [
            OrdemServico.descricao.icontains(termo, autoescape=True),
            OrdemServico.status_os.icontains(termo, autoescape=True),
            OrdemServico.prioridade.icontains(termo, autoescape=True),
            OrdemServico.categoria.icontains(termo, autoescape=True),
            Usuario.nome.icontains(termo, autoescape=True),
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
    return render_template(
        'ordens_servico.html',
        ordens=lista_ordens,
        termo=termo,
        excluidos=excluidos,
    )


@app.route('/servico/ordens/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_ordem_view():
    if request.method == "POST":
        responsavel_id = request.form.get("responsavel_id")
        descricao = request.form.get("descricao", "").strip()
        categoria = request.form.get("categoria", "")
        setor_id = request.form.get("setor_id", "")
        equipamentos_ids = request.form.getlist("equipamentos_ids")
        status_os = request.form.get("status_os")
        prioridade = request.form.get("prioridade")
        custo_total = request.form.get("custo_total")
        data_solicitacao = request.form.get("data_solicitacao")
        data_execucao = request.form.get("data_execucao")

        if tabela_ordens_servico.salvar(
            0,
            responsavel_id,
            descricao,
            status_os,
            prioridade,
            custo_total,
            data_solicitacao,
            data_execucao,
            categoria,
            setor_id,
            equipamentos_ids,
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
    )


@app.route('/servico/ordens/<int:ordem_id>')
@login_required
def detalhes_ordem_servico(ordem_id):
    ordem_servico = tabela_ordens_servico.select_ordem_id(ordem_id)
    if not ordem_servico or not ordem_servico.status_delete:
        flash("Ordem de serviço não encontrada", "error")
        return redirect(url_for("ordens_servico_lista_view"))

    return render_template("ordem_servico_detalhes.html", ordem=ordem_servico)


@app.route('/servico/ordens/excluir/<int:ordem_id>', methods=['POST'])
@login_required
def excluir_ordem_servico(ordem_id):
    ordem_servico = tabela_ordens_servico.select_ordem_id(ordem_id)
    if not ordem_servico or not ordem_servico.status_delete:
        flash("Ordem de serviço não encontrada", "error")
        return redirect(url_for("ordens_servico_lista_view"))

    ordem_servico.status_delete = False
    try:
        db_session.commit()
        flash("Ordem de serviço excluída com sucesso", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception("Erro ao excluir ordem de serviço %s", ordem_id)
        flash("Erro ao excluir a ordem de serviço", "error")
    return redirect(url_for("ordens_servico_lista_view"))


@app.route('/servico/ordens/restaurar/<int:ordem_id>', methods=['POST'])
@login_required
def restaurar_ordem_servico(ordem_id):
    ordem_servico = tabela_ordens_servico.select_ordem_id(ordem_id)
    if not ordem_servico or ordem_servico.status_delete:
        flash("Ordem de serviço excluída não encontrada", "error")
        return redirect(url_for("listar_ordens_servico_excluidos"))

    ordem_servico.status_delete = True
    try:
        db_session.commit()
        flash("Ordem de serviço restaurada com sucesso", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception("Erro ao restaurar ordem de serviço %s", ordem_id)
        flash("Erro ao restaurar a ordem de serviço", "error")
    return redirect(url_for("listar_ordens_servico_excluidos"))


@app.route('/servico/ordens/editar/<int:ordem_id>', methods=['GET', 'POST'])
@login_required
def editar_ordem_servico(ordem_id):
    ordem_servico = tabela_ordens_servico.select_ordem_id(ordem_id)
    if not ordem_servico:
        flash("Ordem de serviço não encontrada", "error")
        return redirect(url_for("ordens_servico_lista_view"))

    if request.method == "POST":
        responsavel_id = request.form.get("responsavel_id")
        descricao = request.form.get("descricao", "").strip()
        categoria = request.form.get("categoria", "")
        setor_id = request.form.get("setor_id", "")
        equipamentos_ids = request.form.getlist("equipamentos_ids")
        status_os = request.form.get("status_os")
        prioridade = request.form.get("prioridade")
        custo_total = request.form.get("custo_total")
        data_execucao = request.form.get("data_execucao")

        if not descricao:
            flash("Preencha a descrição da ordem de serviço", "error")
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

        if data_execucao:
            try:
                data_execucao = datetime.strptime(data_execucao, "%Y-%m-%d").date()
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
            flash("A data de execução não pode ser anterior à data da solicitação", "error")
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

        ordem_servico.responsavel_id = responsavel_id
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
        equipamentos_selecionados=[
            associacao.equipamento_id
            for associacao in ordem_servico.equipamentos_associados
        ],
    )

@app.route('/setor', methods=['GET'])
@login_required
def setor():
    termo = request.args.get("q", "").strip()[:100]
    lista_setores = consultar_setores(True, termo)
    return render_template('setor.html', setores=lista_setores, termo=termo)


@app.route('/setor/excluidos', methods=['GET'])
@login_required
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

        if tabela_setor.salvar(nome, descricao):
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

        setor.nome = nome
        setor.descricao = descricao
        db_session.commit()
        flash("Setor atualizado com sucesso", "success")
        return redirect(url_for("setor"))

    return render_template("setor.html", setores=[], editar=setor)


@app.route('/setor/excluir/<setor_id>', methods=['GET', 'POST'])
@roles_required("admin")
def excluir_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if setor:
        setor.status_delete = False
        db_session.commit()
    return redirect(url_for('setor'))


@app.route('/setor/restaurar/<setor_id>', methods=['GET', 'POST'])
@roles_required("admin")
def restaurar_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if setor:
        setor.status_delete = True
        db_session.commit()
    return redirect(url_for('listar_setores_excluidos'))


@app.route('/funcionarios', methods=['GET'])
@roles_required("admin")
def funcionarios():
    termo = request.args.get("q", "").strip()[:100]
    consulta = select(Usuario).where(Usuario.papel == "usuario")
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
    if not usuario or usuario.papel != "usuario":
        flash("Funcionário não encontrado", "error")
        return redirect(url_for("funcionarios"))

    setores = tabela_setor.select_ativos()
    if request.method == "POST":
        setor_id = request.form.get("setor")
        funcao = request.form.get("funcao", "").strip()

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

        usuario.setor = setor
        usuario.funcao = funcao
        try:
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
    if not usuario or usuario.papel != "usuario":
        flash("Funcionário não encontrado", "error")
        return redirect(url_for("funcionarios"))

    usuario.ativo = False
    try:
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
    if not usuario or usuario.papel != "usuario":
        flash("Funcionário não encontrado", "error")
        return redirect(url_for("funcionarios"))

    usuario.ativo = True
    try:
        db_session.commit()
        flash("Funcionário ativado com sucesso", "success")
    except SQLAlchemyError:
        db_session.rollback()
        app.logger.exception("Erro ao ativar funcionário %s", usuario_id)
        flash("Erro ao ativar o funcionário", "error")
    return redirect(url_for("funcionarios"))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    ordens_servico = tabela_ordens_servico.select_quantidade_total()
    equipamentos = tabela_equipamento.select_quantidade_total()
    setores = tabela_setor.select_quantidade_total()
    usuarios_comuns = tabela_usuario.select_quantidade_comuns()
    ordens_status = tabela_ordens_servico.select_ordem_status()

    return render_template(
        "dashboard.html",
        total_ordens_servico=ordens_servico,
        total_equipamentos=equipamentos,
        total_setores=setores,
        total_usuarios=usuarios_comuns,
        ordens_status=ordens_status,
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
