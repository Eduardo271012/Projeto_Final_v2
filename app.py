from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from banco import tabela_equipamento, tabela_funcionario, tabela_ordens_servico, tabela_setor
from database import Funcionario, Setor, db_session, Usuario
from functools import wraps


app = Flask(__name__)
app.secret_key = "quarks-solucoes"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db_session.get(Usuario, int(user_id))


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
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()

        if not nome and not email and not senha:
            flash("Preencha o nome, email, senha", "error")
            return redirect(url_for("registro"))
        usuario_sql = select(Usuario).where(Usuario.email == email)
        usuario_email = db_session.execute(usuario_sql).scalar_one_or_none()
        if usuario_email:
            flash("E-mail já cadastrado", "error")
            return redirect(url_for("registro"))
        try:
            novo_usuario = Usuario(
                nome = nome,
                email = email
            )
            novo_usuario.set_password(senha)
            db_session.add(novo_usuario)
            db_session.commit()
            flash("Usuário criado com sucesso", "success")
        except SQLAlchemyError as e:
            flash("Erro no banco")
            return redirect(url_for("registro"))
        except SQLAlchemyError as e:
            flash(f"Erro ao registrar", "error")
            flash("Erro ao registrar")
            return render_template("registro.html")

    return render_template("login.html", registro=request.args.get("registro") == "True")


@app.route('/equipamentos')
@login_required
def equipamentos():
    lista_equipamentos = tabela_equipamento.select_ativos()
    return render_template('equipamento.html', equipamentos=lista_equipamentos)


@app.route('/equipamentos/excluidos')
@login_required
def listar_equipamentos_excluidos():
    lista_equipamentos = tabela_equipamento.select_excluidos()
    return render_template('equipamento.html', equipamentos=lista_equipamentos, excluidos=1)


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
    lista_ordens = tabela_ordens_servico.select_todas()
    return render_template('ordens_servico.html', ordens=lista_ordens)


@app.route('/servico/ordens/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_ordem_view():
    if request.method == "POST":
        responsavel_id = request.form.get("responsavel_id")
        descricao = request.form.get("descricao", "").strip()
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
        ):
            return redirect(url_for("ordens_servico_lista_view"))

    funcionarios_tupla = tabela_funcionario.select_funcionarios()
    funcionarios_locais = [f[0] if isinstance(f, tuple) else f for f in funcionarios_tupla]
    lista_ordens = tabela_ordens_servico.select_todas()
    return render_template('ordens_servico.html', funcionarios=funcionarios_locais, ordens=lista_ordens)

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
        status_os = request.form.get("status_os")
        prioridade = request.form.get("prioridade")
        custo_total = request.form.get("custo_total")
        data_execucao = request.form.get("data_execucao")

        ordem_servico.responsavel_id = responsavel_id
        ordem_servico.descricao = descricao
        ordem_servico.status_os = status_os
        ordem_servico.prioridade = prioridade
        ordem_servico.custo_total = custo_total
        ordem_servico.data_execucao = data_execucao

        db_session.commit()
        flash("Ordem de Serviço editada com sucesso", "success")
        return redirect(url_for("ordens_servico_lista_view"))

    return render_template('ordens_servico.html', editar=ordem_servico)

@app.route('/setor', methods=['GET'])
@login_required
def setor():
    lista_setores = tabela_setor.select_ativos()
    return render_template('setor.html', setores=lista_setores)


@app.route('/setor/excluidos', methods=['GET'])
@login_required
def listar_setores_excluidos():
    lista_setores = tabela_setor.select_excluidos()
    return render_template('setor.html', setores=lista_setores, excluidos=1)


@app.route('/setor/cadastro', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def excluir_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if setor:
        setor.status_delete = False
        db_session.commit()
    return redirect(url_for('setor'))


@app.route('/setor/restaurar/<setor_id>', methods=['GET', 'POST'])
@login_required
def restaurar_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if setor:
        setor.status_delete = True
        db_session.commit()
    return redirect(url_for('listar_setores_excluidos'))


@app.route('/funcionarios', methods=['GET'])
@login_required

def funcionarios():
    lista_funcionarios = tabela_funcionario.select_todos()
    return render_template('funcionario.html', funcionarios=lista_funcionarios)

@app.route('/funcionarios/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_funcionario():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf = request.form.get("cpf", "").strip()
        email = request.form.get("email", "").strip()
        setor = request.form.get("setor")
        funcao = request.form.get("funcao")

        if not nome or not email or not cpf or not setor or not funcao:
            flash("Preencha todos os campos obrigat?rios", "error")
            return redirect(url_for("cadastro_funcionario"))

        funcionarios = tabela_funcionario.select_todos()
        ultimo_setor = db_session.execute(
            select(Setor.id).order_by(Setor.id.desc()).limit(1)
        ).scalar() or 0

        if tabela_funcionario.validar_funcionario(nome, cpf, email, setor, funcionarios, ultimo_setor):
            return redirect(url_for("cadastro_funcionario"))

        tabela_funcionario.salvar(nome=nome, cpf=cpf, email=email, setor_id=setor, funcao=funcao)
        return redirect(url_for('funcionarios'))

    lista_setores = tabela_setor.select_ativos()
    return render_template('funcionario.html', setores=lista_setores)



@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    ordens_servico = tabela_ordens_servico.select_quantidade_total()
    equipamentos = tabela_equipamento.select_quantidade_total()
    setores = tabela_setor.select_quantidade_total()
    funcionarios = tabela_funcionario.select_quantidade_total()
    ordens_status = tabela_ordens_servico.select_ordem_status()

    return render_template(
        "dashboard.html",
        total_ordens_servico=ordens_servico,
        total_equipamentos=equipamentos,
        total_setores=setores,
        total_funcionarios=funcionarios,
        ordens_status=ordens_status,
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
