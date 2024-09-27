
from flask import Flask, flash, jsonify, redirect, render_template, request, session
import mysql.connector
import secure as sc


app = Flask(__name__)

# Certifica de que os templates sejam recarregados automaticamente
app.config["TEMPLATES_AUTO_RELOAD"] = True

my_pass = sc.my_conn()

db_config = {
    "host": "localhost",
    "user": "root",
    "password": f"{my_pass}",
    "database": "modelosclassicos"
}

#inicio index..............................................................
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/ultimas_alteracoes")
def ultimas_alteracoes():
   
    try:
        
        conn = mysql.connector.connect(**db_config)# Conecte ao banco de dados MySQL
        cursor = conn.cursor()# Crie um cursor

        #cria a variavel query quando a instrução é muito longa... fica mais facil a leitura
        my_query = """
        SELECT 
            customerName, 
            contactLastName, 
            contactFirstName, 
            phone, 
            creditLimit 
        FROM clientes ORDER BY creditLimit DESC LIMIT 15"""

        cursor.execute(my_query)#executa a query...
        clientes = cursor.fetchall()# Recupera todos os resultados da consulta 

        # Feche o cursor e a conexão
        cursor.close()
        conn.close()

        # Renderize o template HTML com os dados dos clientes
        return render_template("ultimas_alteracoes.html", clientes=clientes)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500

#inicio clientes..........................................................
@app.route("/clientes/<string:orderby>", methods=["GET"])
def clientes(orderby):
    try:
        # Conecte ao banco de dados MySQL
        conn = mysql.connector.connect(**db_config)


        cursor = conn.cursor()
        # Certifique-se de validar 'orderby' para evitar injeção de SQL!        
        valid_columns = ["customerNumber", "customerName"]#validando somente as colunas permitidas
     
        if orderby not in valid_columns:
            return "Coluna de ordenação inválida", 400
        
        #carregamento a tabela clientes
        # Use formatação de string segura para a consulta SQL
        my_query = f"SELECT * FROM clientes ORDER BY {orderby}"
        cursor.execute(my_query)
        clientes = cursor.fetchall()
        cursor.close()

        #iniciando a tabela top 10
        cursor = conn.cursor()
        query = """
        SELECT 
            cli.customerNumber, cli.customerName, SUM(pag.amount) AS totalCompras 
        FROM 
            clientes AS cli JOIN pagamentos AS pag 
        ON 
            cli.customerNumber = pag.customerNumber 
        GROUP BY 
            cli.customerNumber, cli.customerName 
        ORDER BY 
            totalCompras DESC LIMIT 10;"""
        
        cursor.execute(query)
        bestclientes = cursor.fetchall()
        cursor.close()

        #fechando a conexão de ambas as querys
        conn.close()

        # Renderize o template HTML com os dados da tb clientes e tb top 10
        return render_template("clientes.html", clientes=clientes, bestclientes=bestclientes)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500   
    
#inicio Detalhe clientes..................................................
@app.route("/clientedetalhes/<int:customerNumber>", methods=["GET", "POST"])
def clientedetalhes(customerNumber):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE customerNumber = %s", (customerNumber,))
        clientes = cursor.fetchone()
        cursor.close()

        cursor2 = conn.cursor() 
        cursor2.execute("SELECT * FROM pedidos WHERE customerNumber = %s", (customerNumber,))
        pedidos = cursor2.fetchall()
        cursor2.close()
        
        conn.close()

        return render_template("clientedetalhes.html", clientes=clientes, pedidos=pedidos )
    
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500 
    
#Pedidos.....................................................................    
@app.route("/pedidos")
def pedidos():

    try: 
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos")
        pedidos = cursor.fetchall()

        cursor.close()
        conn.close()

        #aviso = f'  Em construção...'
        return render_template("pedidos.html", pedidos=pedidos)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500

#Detalhe Pedidos............................................................
@app.route("/detalhespedido/<int:orderNumber>", methods=["GET", "POST"])
def detalhespedido(orderNumber):
    try:
        # Consulta SQL para obter os detalhes do pedido
        conn = mysql.connector.connect(**db_config)
        my_query = """
        SELECT
            d.productCode AS CodigoProduto,
            p.productName AS NomeProduto,
            d.quantityOrdered AS Quantidade,
            d.priceEach AS PrecoUnitario,
            (d.quantityOrdered * d.priceEach) AS Subtotal
        FROM
            detalhespedido d
            JOIN produtos p ON d.productCode = p.productCode
        WHERE
            d.orderNumber = %s
        """  
        cursor = conn.cursor()
        cursor.execute(my_query, (orderNumber,))
        detPedido = cursor.fetchall()
        
    #Segundo parametro.........................................

    # Consulta SQL para calcular o total do pedido
        sql_total = """
        SELECT
            SUM(d.quantityOrdered * d.priceEach) AS Total
        FROM
            detalhespedido d
        WHERE
            d.orderNumber = %s
        """

        # Executa a consulta com o parâmetro do número do pedido para obter o total
        cursor.execute(sql_total, (orderNumber,))
        total_result = cursor.fetchone()
        total_pedido = total_result[0]

        cursor.close()
        conn.close()

        return render_template("detalhespedido.html", detPedido=detPedido, total_pedido=total_pedido )
    
    except  mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500 
    
#Produtos...................................................................   
@app.route("/produtos")
def produtos():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos ")
        produtos = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template("produtos.html", produtos=produtos)
    
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500 

#Funcionários..............................................................    
@app.route("/funcionarios/<string:orderby>", methods=["GET", "POST"])
def funcionarios(orderby):
    try:

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

 # Certifique-se de validar 'orderby' para evitar injeção de SQL!
        valid_columns = ["employeeNumber", "firstName", "officeCode"]
        if orderby not in valid_columns:
            return "Coluna de ordenação inválida", 400

          # Use formatação de string segura para a consulta SQL
        query = f"SELECT * FROM funcionarios ORDER BY {orderby}"
        cursor.execute(query)

        funcionarios = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template("funcionarios.html", funcionarios=funcionarios)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500

#Escritórios
@app.route("/escritorios")
def escritorios():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM escritorios")
        escritorios = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template("escritorios.html", escritorios=escritorios)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500

#staff do escritório
@app.route("/func_office/<string:officeCode>", methods=["GET", "POST"])
def func_office(officeCode):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM funcionarios WHERE officeCode = %s ", (officeCode ,))

        funcionarios = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template("func_office.html", funcionarios=funcionarios)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500


#inicio dos inserts funcionarios............................................... 
@app.route("/cad_func", methods=["GET", "POST"])
def cad_func():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT officeCode, city FROM escritorios ")
        results = cursor.fetchall()
        cursor.close()

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT jobTitle FROM funcionarios LIMIT 7")
        allcargos = cursor.fetchall()
        cursor.close()
      
        #abre um novo cursor
        cursor = conn.cursor()
        #derscobrir o último id 'employeeNumber' da tabela funcionários
        cursor.execute("SELECT employeeNumber FROM funcionarios ORDER BY employeeNumber DESC LIMIT 1")
        last_id = cursor.fetchone()
        if last_id:
            last_id = last_id[0] + 1  # Extrai o valor da tupla e adiciona 1
        else:
            last_id = 1  # Caso não haja registros, comece com 1 como o primeiro employeeNumber
        cursor.close()
       
        if request.method == "POST":
  
            nome = request.form.get("firstName" )
            sobrenome = request.form.get("lastName")
            ramal = request.form.get("extension")
            email = request.form.get("email")
            filial = request.form.get("officeCode")
            reporta = "1143"
            cargo = request.form.get("jobTitle")

        # Adicionar a entrada do usuário no banco de dados
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO funcionarios (employeeNumber, lastName , firstName , extension , email , officeCode , reportsTo , jobTitle  ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (last_id, sobrenome, nome, ramal, email, filial, reporta, cargo))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect("funcionarios/employeeNumber")

        return render_template("cad_func.html", last_id=last_id, results=results, allcargos=allcargos )

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500
    
#edit funcionario..............................................................
@app.route("/edit_func/<int:employeeNumber>", methods=["GET", "POST"])
def edit_func(employeeNumber):

    if request.method == "GET":

        # Buscar o usuário no banco de dados
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM funcionarios WHERE employeeNumber  = %s", (employeeNumber,))
        funcionario = cursor.fetchone()
        cursor.close()
        print(funcionario)

        # Verifica se o usuário existe
        if not funcionario:
            flash("Usuário não encontrado.")
            return redirect("/")

        return render_template("edit_func.html", funcionario=funcionario)

    elif request.method == "POST":
        nome = request.form.get("firstName")
        sobrenome = request.form.get("lastName")
        ramal = request.form.get("extension")
        email = request.form.get("email")
        filial = request.form.get("officeCode")
        reportar = request.form.get("reportsTo")
        cargo = request.form.get("jobTitle")

        # Atualizar as informações do usuário no banco de dados, incluindo a data de alteração
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("UPDATE funcionarios SET lastName = %s, firstName = %s, extension = %s, email = %s, officeCode = %s, reportsTo = %s, jobTitle = %s WHERE employeeNumber  = %s",
                       (sobrenome, nome, ramal, email, filial, reportar, cargo, employeeNumber))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/funcionarios/employeeNumber")

#Deletar funcionário..................................................    
@app.route("/del_func/<int:employeeNumber>", methods=["GET", "POST"])
def del_func(employeeNumber):
    if request.method == "GET":
        # Buscar o usuário no banco de dados
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM funcionarios WHERE employeeNumber = %s", (employeeNumber,))
        funcionario = cursor.fetchone()
        cursor.close()
        conn.close()
        print(funcionario)
        
        # Verifica se o usuário existe
        if not funcionario:
            flash("Usuário não encontrado.")
            return redirect("/funcionarios/employeeNumber")

        return render_template("del_func.html", funcionario=funcionario)

    elif request.method == "POST":

        # Deletar o usuário do banco de dados
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM funcionarios WHERE employeeNumber = %s", (employeeNumber,))
        conn.commit()
        cursor.close()
        conn.close()
        #flash("Usuário excluído com sucesso!")

        return redirect("/funcionarios/employeeNumber")

@app.route("/pagamentos")
def pagamentos():

    aviso = f'  Em construção...'
    return render_template("pagamentos.html", aviso=aviso)

@app.route("/linhadeprodutos")
def linhadeprodutos():

    aviso = f'  Em construção...'
    return render_template("linhadeprodutos.html", aviso=aviso)

if __name__ == "__main__":
    app.run(debug=True)
   