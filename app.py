from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager
from sqlalchemy import select

from banco import tabela_equipamento, tabela_funcionario, tabela_ordens_servico, tabela_setor
from database import Funcionario, Setor, db_session

app = Flask(__name__)
app.secret_key = "quarks-solucoes"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db_session.get(Funcionario, int(user_id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/equipamentos')
def equipamentos():
    lista_equipamentos = tabela_equipamento.select_ativos()
    return render_template('equipamento.html', equipamentos=lista_equipamentos)


@app.route('/equipamentos/excluidos')
def listar_equipamentos_excluidos():
    lista_equipamentos = tabela_equipamento.select_excluidos()
    return render_template('equipamento.html', equipamentos=lista_equipamentos, excluidos=1)


@app.route('/equipamentos/cadastro', methods=['GET', 'POST'])
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
def excluir_equipamento(equipamento_id):
    equipamento = tabela_equipamento.select_id(equipamento_id)
    if equipamento and equipamento.status_delete:
        equipamento.status_delete = False
        db_session.commit()
    return redirect(url_for("equipamentos"))


@app.route('/equipamentos/restaurar/<int:equipamento_id>', methods=['GET', 'POST'])
def restaurar_equipamento(equipamento_id):
    equipamento = tabela_equipamento.select_id(equipamento_id)
    if equipamento and not equipamento.status_delete:
        equipamento.status_delete = True
        db_session.commit()
    return redirect(url_for("listar_equipamentos_excluidos"))


@app.route('/ordens_servico', methods=['GET'])
def ordens_servico_lista_view():
    lista_ordens = tabela_ordens_servico.select_todas()
    return render_template('ordens_servico.html', ordens=lista_ordens)


@app.route('/servico/ordens/cadastro', methods=['GET', 'POST'])
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


@app.route('/setor', methods=['GET'])
def setor():
    lista_setores = tabela_setor.select_ativos()
    return render_template('setor.html', setores=lista_setores)


@app.route('/setor/excluidos', methods=['GET'])
def listar_setores_excluidos():
    lista_setores = tabela_setor.select_excluidos()
    return render_template('setor.html', setores=lista_setores, excluidos=1)


@app.route('/setor/cadastro', methods=['GET', 'POST'])
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
def excluir_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if setor:
        setor.status_delete = False
        db_session.commit()
    return redirect(url_for('setor'))


@app.route('/setor/restaurar/<setor_id>', methods=['GET', 'POST'])
def restaurar_setor(setor_id):
    setor = tabela_setor.select_id(setor_id)
    if setor:
        setor.status_delete = True
        db_session.commit()
    return redirect(url_for('listar_setores_excluidos'))


@app.route('/funcionarios', methods=['GET'])
def funcionarios():
    lista_funcionarios = tabela_funcionario.select_todos()
    return render_template('funcionario.html', funcionarios=lista_funcionarios)


@app.route('/funcionarios/cadastro', methods=['GET', 'POST'])
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
def dashboard():
    ordens_servico = tabela_ordens_servico.select_quantidade_total()
    equipamentos = tabela_equipamento.select_quantidade_total()
    setores = tabela_setor.select_quantidade_total()
    funcionarios = tabela_funcionario.select_quantidade_total()

    return render_template(
        "dashboard.html",
        total_ordens_servico=ordens_servico,
        total_equipamentos=equipamentos,
        total_setores=setores,
        total_funcionarios=funcionarios,
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
