from flask import Flask, flash, jsonify, redirect, render_template, request, session
import mysql.connector
import secure as sc

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

my_pass = sc.my_conn()

db_config = {
    "host": "localhost",
    "user": "root",
    "password": f"{my_pass}",
    "database": "modelosclassicos"
}

# inicio index..............................................................


@app.route("/")
def index():

    try:

        # Conecte ao banco de dados MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()  # Crie um cursor

        # cria a variavel query quando a instrução é muito longa... fica mais facil a leitura
        my_query = """
        SELECT 
            customerName, 
            contactLastName, 
            contactFirstName, 
            phone, 
            creditLimit 
        FROM clientes ORDER BY creditLimit DESC LIMIT 15"""

        cursor.execute(my_query)  # executa a query...
        clientes = cursor.fetchall()  # Recupera todos os resultados da consulta

        # Feche o cursor e a conexão
        cursor.close()
        conn.close()

        # Renderize o template HTML com os dados dos clientes
        return render_template("index.html", clientes=clientes)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500


# inicio clientes..........................................................
@app.route("/clientes/<string:orderby>", methods=["GET"])
def clientes(orderby):
    try:
        # Conecte ao banco de dados MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Certifique-se de validar 'orderby' para evitar injeção de SQL!
        # validando somente as colunas permitidas
        valid_columns = ["customerNumber", "customerName"]

        if orderby not in valid_columns:
            return "Coluna de ordenação inválida", 400

        # Use formatação de string segura para a consulta SQL
        my_query = f"SELECT * FROM clientes ORDER BY {orderby}"
        cursor.execute(my_query)
        clientes = cursor.fetchall()
        cursor.close()

        # iniciando a segunda instrução
        cursor = conn.cursor()
        query = """
        SELECT 
            cli.customerNumber, 
            cli.customerName, 
            SUM(pag.amount) AS totalCompras 
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

        # fechando a conexão de ambas as querys
        conn.close()

        # Renderize o template HTML com os dados dos clientes
        return render_template("clientes.html", clientes=clientes, bestclientes=bestclientes)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500


# inicio Detalhe clientes..................................................
@app.route("/clientedetalhes/<int:customerNumber>", methods=["GET", "POST"])
def clientedetalhes(customerNumber):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM clientes WHERE customerNumber = %s", (customerNumber,))
        clientes = cursor.fetchone()
        cursor.close()

        cursor2 = conn.cursor()
        cursor2.execute(
            "SELECT * FROM pedidos WHERE customerNumber = %s", (customerNumber,))
        pedidos = cursor2.fetchall()
        cursor2.close()

        conn.close()

        return render_template("clientedetalhes.html", clientes=clientes, pedidos=pedidos)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500


# Pedidos.....................................................................
@app.route("/pedidos")
def pedidos():

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos")
        pedidos = cursor.fetchall()

        cursor.close()
        conn.close()

        # aviso = f'  Em construção...'
        return render_template("pedidos.html", pedidos=pedidos)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500


# Detalhe Pedidos............................................................
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

    # Segundo parametro.........................................

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

        return render_template("detalhespedido.html", detPedido=detPedido, total_pedido=total_pedido)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500


# Produtos...................................................................
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


# Cliente Produtos..........................................................
@app.route("/cliprodutos/<string:productCode>", methods=["GET", "POST"])
def cliprodutos(productCode):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM produtos WHERE productCode = %s", (productCode,))
        cliprodutos = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template("cliprodutos.html", cliprodutos=cliprodutos)

    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return "Erro ao conectar ao banco de dados", 500


@app.route("/funcionarios/<string:orderby>", methods=["GET", "POST"])
def funcionarios(orderby):
    try:

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

 # Certifique-se de validar 'orderby' para evitar injeção de SQL!
        valid_columns = ["employeeNumber", "lastName", "firstName",
                         "extension", "email", "officeCode", "reportsTo", "jobTitle"]
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
