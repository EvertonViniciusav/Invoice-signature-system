import os
import jwt
import datetime
import mysql.connector
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps

# Carregar variáveis do ambiente
load_dotenv()

# Configuração do Flask
app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta")

# Conectar ao banco de dados
def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# Middleware para autenticação de token JWT
def autenticar_token(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"erro": "Token não fornecido"}), 401

        try:
            token = token.split(" ")[1]  # Remove "Bearer "
            dados = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.usuario = dados
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido"}), 401

        return f(*args, **kwargs)

    return decorador

# Middleware para verificar permissões de admin
def autorizar_admin(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if request.usuario.get("tipo") != "admin":
            return jsonify({"erro": "Acesso negado. Permissão insuficiente."}), 403
        return f(*args, **kwargs)

    return decorador

# Rota de teste
@app.route("/", methods=["GET"])
def home():
    return render_template('login.html')

# Rota para cadastro de usuários
@app.route("/cadastro", methods=["POST"])
def cadastrar_usuario():
    dados = request.json
    nome = dados.get("nome")
    cpf = dados.get("cpf")
    senha = dados.get("senha")
    tipo = dados.get("tipo", "usuario")  # Padrão usuário

    if not nome or not cpf or not senha:
        return jsonify({"erro": "Todos os campos são obrigatórios!"}), 400

    senha_hash = generate_password_hash(senha)
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        sql = "INSERT INTO usuarios (nome, cpf, senha, tipo) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (nome, cpf, senha_hash, tipo))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"mensagem": "Usuário cadastrado com sucesso!"})
    except Exception as e:
        return jsonify({"erro": f"Erro ao cadastrar usuário: {str(e)}"}), 500

# Rota para login
@app.route("/login", methods=["GET", "POST"])
def login():

    cpf = request.form.get("cpf")
    senha = request.form.get("senha")

    if not cpf or not senha:
        return jsonify({"erro": "CPF e senha são obrigatórios"}), 400

    try:
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, senha, tipo, status FROM usuarios WHERE cpf = %s", (cpf,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if not usuario or not check_password_hash(usuario["senha"], senha):
            return jsonify({"erro": "CPF ou senha inválidos."}), 401

        if usuario["status"] == "inativo":
            return jsonify({"erro": "Usuário inativo. Contate o administrador."}), 403

        payload = {
            "id": usuario["id"],
            "cpf": cpf,
            "tipo": usuario["tipo"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Rota para listar usuários (Apenas admin pode acessar)
@app.route("/usuarios", methods=["GET"])
@autenticar_token
@autorizar_admin
def listar_usuarios():
    try:
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, cpf, tipo, status FROM usuarios")
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar usuários: {str(e)}"}), 500
    
@app.route("/usuarios/status", methods=["PUT"])
@autenticar_token
def atualizar_status_usuario():
    if request.usuario["tipo"] != "admin":
        return jsonify({"erro": "Acesso negado!"}), 403

    dados = request.json
    cpf = dados.get("cpf")
    novo_status = dados.get("status")

    if not cpf or novo_status not in ["ativo", "inativo"]:
        return jsonify({"erro": "CPF e status são obrigatórios!"}), 400

    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        sql = "UPDATE usuarios SET status = %s WHERE cpf = %s"
        cursor.execute(sql, (novo_status, cpf))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"erro": "Usuário não encontrado!"}), 404

        cursor.close()
        conn.close()
        return jsonify({"mensagem": f"Status do usuário {cpf} atualizado para {novo_status}!"})
    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar status: {str(e)}"}), 500


# Rota para listar notas fiscais (Todos os usuários autenticados podem acessar)
@app.route("/notas", methods=["GET"])
@autenticar_token
def listar_notas():
    try:
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)

        if request.usuario["tipo"] == "admin":
            # Admin pode ver todas as notas
            cursor.execute("SELECT * FROM notas_fiscais")
        else:
            # Motorista só pode ver notas pendentes
            cursor.execute("SELECT * FROM notas_fiscais WHERE status IN ('pendente')")

        notas = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(notas)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar notas fiscais: {str(e)}"}), 500

# Rota para atualizar o status de uma nota fiscal
@app.route("/notas/atualizar", methods=["PUT"])
@autenticar_token
def atualizar_status_nota():
    dados = request.json
    nota_id = dados.get("nota_id")
    novo_status = dados.get("status")

    # Verificar se o status é válido
    if novo_status not in ["pendente", "assinada"]:
        return jsonify({"erro": "Status inválido. Use 'pendente' ou 'assinada'"}), 400

    try:
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)

        # Verificar se a nota existe
        cursor.execute("SELECT * FROM notas_fiscais WHERE id = %s", (nota_id,))
        nota = cursor.fetchone()

        if not nota:
            return jsonify({"erro": "Nota fiscal não encontrada"}), 404

        # Atualizar o status da nota
        sql = "UPDATE notas_fiscais SET status = %s WHERE id = %s"
        cursor.execute(sql, (novo_status, nota_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"mensagem": "Status da nota atualizado com sucesso!"})
    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar status da nota: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
