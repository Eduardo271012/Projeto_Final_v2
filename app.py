from flask import Flask, render_template, redirect, url_for, flash, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

# from banco import
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/clientes')
def clientes():
    return render_template('cliente.html')


@app.route('/clientes/cadastro', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == "POST":
        # 1 - Pegar os valores digitados no form
        nome = request.form.get("nome").strip()
        data_nascimento = request.form.get("data_nascimento").strip()
        telefone = request.form.get("telefone").strip()
        email = request.form.get("email").strip()
        cpf_cnpj = request.form.get("cpf_cnpj").strip()
        departamento = request.form.get("departamento").strip()

        # 2 - Verificar se foi digitado
        if not nome:
            flash("Preencha o nome", "error")
            return redirect(url_for("cadastro_clientes"))
        if not data_nascimento:
            flash("Preencha a data de nascimento", "error")
            return redirect(url_for("cadastro_clientes"))
        if not telefone:
            flash("Preencha o telefone", "error")
            return redirect(url_for("cadastro_clientes"))
        if not email:
            flash("Preencha o email", "error")
            return redirect(url_for("cadastro_clientes"))
        if not cpf_cnpj:
            flash("Preencha o CPF ou CNPJ", "error")
            return redirect(url_for("cadastro_clientes"))
        if not departamento:
            flash("Selecione o departamento", "error")
            return redirect(url_for("cadastro_clientes"))

        return redirect(url_for('clientes'))

        # 3 - Salvar no banco
    # tabela_time.salvar(nome=nome, numero_camisa=numero_camisa, posicao=posicao, time_id=time_id)
    return render_template('cliente.html')


@app.route('/equipamentos')
def equipamentos():
    return render_template('equipamento.html')


@app.route('/equipamentos/cadastro', methods=['GET', 'POST'])
def cadastro_equipamento():
    if request.method == "POST":
        nome_equipamento = request.form.get("nome_equipamento").strip()
        quantidade_estoque = request.form.get("quantidade_estoque").strip()
        modelo = request.form.get("modelo").strip()
        numero_serie = request.form.get("numero_serie").strip()

        if not nome_equipamento:
            flash("Preencha o nome", "error")
            return redirect(url_for("cadastro_equipamentos"))
        if not quantidade_estoque:
            flash("Preencha a quantidade", "error")
            return redirect(url_for("cadastro_equipamentos"))
        if not modelo:
            flash("Preencha o modelo", "error")
            return redirect(url_for("cadastro_equipamentos"))
        if not numero_serie:
            flash("Preencha o número de série", "error")
            return redirect(url_for("cadastro_equipamentos"))

    return render_template('equipamento.html')


@app.route('/ordens', methods=['GET', 'POST'])
def ordem():
    return render_template('ordens_servico.html')

@app.route('/os/cadastro', methods=['GET', 'POST'])
def cadastro_ordem():
    if request.method == "POST":
        titulo_os = request.form.get("titulo_os").strip()
        cliente = request.form.get("cliente").strip()
        descricao = request.form.get("descricao").strip()
        status = request.form.get("status").strip()
        prioridade = request.form.get("prioridade").strip()
        data_solicitacao = request.form.get("data_solicitacao").strip()
        data_entrega = request.form.get("data_entrega").strip()

        if not titulo_os:
            flash("Preencha o título da OS", "error")
            return redirect(url_for("cadastro_os"))
        if not cliente:
            flash("Preencha o nome do cliente", "error")
            return redirect(url_for("cadastro_os"))
        if not descricao:
            flash("Descreva a OS", "error")
            return redirect(url_for("cadastro_os"))
        if not status:
            flash("Preencha o status da OS", "error")
            return redirect(url_for("cadastro_os"))
        if not prioridade:
            flash("Preencha a prioridade da OS", "error")
            return redirect(url_for("cadastro_os"))
        if not data_solicitacao:
            flash("Preencha a data da solicitação", "error")
            return redirect(url_for("cadastro_os"))
        if not data_entrega:
            flash("Preencha a data da entrega", "error")
            return redirect(url_for("cadastro_os"))

    return render_template('ordens_servico.html')


@app.route('/acesso', methods=['GET', 'POST'])
def acesso():
    return render_template('acesso.html')


@app.route('/setor', methods=['GET', 'POST'])
def setor():
    return render_template('setor.html')


@app.route('/setores/cadastro', methods=['GET', 'POST'])
def cadastro_setor():
    if request.method == "POST":
        nome = request.form.get("nome").strip()
        descricao = request.form.get("descricao").strip()

        if not nome:
            flash("Preencha o nome", "error")
            return redirect(url_for("cadastro_setores"))
        if not descricao:
            flash("Adicione a descrição", "error")
            return redirect(url_for("cadastro_setores"))

    return render_template('setor.html')


@app.route('/funcionarios')
def funcionarios():
    return render_template('funcionario.html')


@app.route('/funcionarios/cadastro', methods=['GET', 'POST'])
def cadastro_funcionario():
    if request.method == "POST":
        nome = request.form.get("nome").strip()
        cpf = request.form.get("cpf").strip()
        email = request.form.get("email").strip()
        setor = request.form.get("setor").strip()
        funcao = request.form.get("funcao").strip()

        if not nome:
            flash("Preencha o nome", "error")
            return redirect(url_for("cadastro_funcionarios"))
        if not email:
            flash("Preencha o email", "error")
            return redirect(url_for("cadastro_funcionarios"))
        if not cpf:
            flash("Preencha o CPF", "error")
            return redirect(url_for("cadastro_funcionarios"))
        if not setor:
            flash("Selecione o setor", "error")
            return redirect(url_for("cadastro_funcionarios"))
        if not funcao:
            flash("Selecione a função", "error")
            return redirect(url_for("cadastro_funcionarios"))

    return render_template('funcionario.html')


# Iniciar aplicação web
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
# Nada deve ser colocado abaixo
