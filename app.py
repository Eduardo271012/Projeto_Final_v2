from flask import Flask, render_template, redirect, url_for, flash, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from banco import *
from validate_docbr import CPF, CNPJ # Bilioteca para validar dados de documentos brasileiros
from database import *
import re
from datetime import datetime, date
from database import *
from banco import tabela_setor, tabela_equipamento, tabela_funcionario, tabela_ordens_servico
from flask_login import LoginManager, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

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


# --- ROTAS DE CLIENTES ---
@app.route('/clientes', methods=['GET'])
def clientes():
    return render_template('cliente.html')

@app.route('/clientes/cadastro', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == "POST":
        # 1 - Pegar os valores digitados no formulário
        nome = request.form.get("nome", "").strip()
        data_nascimento = request.form.get("data_nascimento", "").strip()
        telefone = request.form.get("telefone", "").strip()
        email = request.form.get("email", "").strip().lower()
        cpf_cnpj = request.form.get("cpf_cnpj", "").strip()
        departamento = request.form.get("departamento").strip()

        erro = tabela_cliente.validar_cliente(nome=nome, data_nascimento=data_nascimento, telefone=telefone, email=email, cpf_cnpj=cpf_cnpj, departamento=departamento)
        if erro:
            return redirect(url_for("cadastro_cliente"))

        # 3 - Salvar no banco
        tabela_cliente.salvar(nome=nome, data_nascimento=data_nascimento, telefone=telefone, email=email, cpf_cnpj=cpf_cnpj)
    return render_template('cliente.html')

@app.route('/equipamentos')
def equipamentos():
    lista_equipamentos = tabela_equipamento.select_todos()
    return render_template('equipamento.html', equipamentos=lista_equipamentos)

@app.route('/equipamentos/cadastro', methods=['GET', 'POST'])
def cadastro_equipamento():
    if request.method == "POST":
        nome = request.form.get("nome_equipamento", "").strip()
        quantidade = request.form.get("quantidade_estoque", "").strip()
        modelo = request.form.get("modelo", "").strip()
        custo = request.form.get("custo_equipamento", "").strip()

        # 1. Executa a validação
        if tabela_equipamento.validar_equipamento(nome, quantidade, modelo, custo) is True:
            return redirect(url_for("cadastro_equipamento"))

        # 2. Se tudo estiver certo, salva e manda para a listagem
        if tabela_equipamento.salvar(nome, modelo, quantidade, custo):
            return redirect(url_for("equipamentos"))

    lista_equipamentos = tabela_equipamento.select_todos()
    return render_template('equipamento.html', equipamentos=lista_equipamentos)


# --- ROTAS DE ORDENS DE SERVIÇO ---
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

        if tabela_ordens_servico.salvar(0, responsavel_id, descricao, status_os, prioridade, custo_total, data_solicitacao, data_execucao):
            return redirect(url_for("ordens_servico_lista_view"))

    funcionarios_tupla = tabela_funcionario.select_funcionarios()
    funcionarios_locais = [f[0] if isinstance(f, tuple) else f for f in funcionarios_tupla]

    lista_ordens = tabela_ordens_servico.select_todas()


    return render_template('ordens_servico.html', funcionarios=funcionarios_locais, ordens=lista_ordens)


# --- ROTAS DE SETORES ---
@app.route('/setor', methods=['GET'])
def setor():
    lista_setores = tabela_setor.select_todos()
    return render_template('setor.html', setores=lista_setores)


@app.route('/setor/cadastro', methods=['GET', 'POST'])
def cadastro_setor():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()

        # 1. Executa a validação do script tabela_setor
        if tabela_setor.validar_setor(nome, descricao):
            return redirect(url_for("cadastro_setor"))

        # 2. Se não houver erros de validação, salva fisicamente no banco
        if tabela_setor.salvar(nome, descricao):
            return redirect(url_for("setor"))  # Redireciona para a lista caso salve com sucesso

        # Se for requisição GET, busca a lista para renderizar a tabela abaixo do form
    lista_setores = tabela_setor.select_todos()
    return render_template('setor.html', setores=lista_setores)


# --- ROTAS DE FUNCIONÁRIOS ---
@app.route('/funcionarios', methods=['GET'])
def funcionarios():
    # MUDANÇA AQUI: Guardamos o resultado em 'lista_funcionarios'
    lista_funcionarios = tabela_funcionario.select_todos()

    # Passamos 'lista_funcionarios' para a variável 'funcionarios' que o HTML espera
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
            flash("Preencha todos os campos obrigatórios", "error")
            return redirect(url_for("cadastro_funcionario"))

        # Lógica para salvar no banco futuramente...
        tabela_funcionario.salvar(nome=nome, cpf=cpf, email=email, setor_id=setor, funcao=funcao)
        return redirect(url_for('funcionarios'))

    # ADICIONE ISTO AQUI: Busca todos os setores para carregar no componente <select> do HTML
    from database import Setor, db_session
    from sqlalchemy import select

    setores_sql = select(Setor)
    lista_setores = db_session.execute(setores_sql).scalars().all()

    # Enviamos a lista de setores capturada para a página HTML
    return render_template('funcionario.html', setores=lista_setores)

# --- DEMAIS ROTAS ---
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')





# Iniciar aplicação web
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
# Nada deve ser colocado abaixo
