
from flask import Flask, render_template, redirect, url_for, flash, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
#from banco import
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
            return redirect(url_for("cadastro_cliente"))
        if not data_nascimento:
            flash("Preencha a data de nascimento", "error")
            return redirect(url_for("cadastro_cliente"))
        if not telefone:
            flash("Preencha o telefone", "error")
            return redirect(url_for("cadastro_cliente"))
        if not email:
            flash("Preencha o email", "error")
            return redirect(url_for("cadastro_cliente"))
        if not cpf_cnpj:
            flash("Preencha o CPF ou CNPJ", "error")
            return redirect(url_for("cadastro_cliente"))
        if not departamento:
            flash("Selecione o departamento", "error")
            return redirect(url_for("cadastro_cliente"))

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
            return redirect(url_for("cadastro_equipamento"))
        if not quantidade_estoque:
            flash("Preencha a quantidade", "error")
            return redirect(url_for("cadastro_equipamento"))
        if not modelo:
            flash("Preencha o modelo", "error")
            return redirect(url_for("cadastro_equipamento"))
        if not numero_serie:
            flash("Preencha o número de série", "error")
            return redirect(url_for("cadastro_equipamento"))

    return render_template('equipamento.html')

@app.route('/servico/ordens', methods=['GET', 'POST'])
def ordens_servico():
    return render_template('ordens_servico.html')

@app.route('/acesso', methods=['GET', 'POST'])
def acesso():
    return render_template('acesso.html')

@app.route('/setor', methods=['GET', 'POST'])
def setor():
    return render_template('setor.html')

@app.route('/funcionarios/cadastro', methods=['GET', 'POST'])
def cadastro_funcionario():
    return render_template('funcionario.html')



# Iniciar aplicação web
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
# Nada deve ser colocado abaixo