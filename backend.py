from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configuração do Flask
app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# Conectar ao banco de dados
def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# Rota de teste
@app.route("/", methods=["GET"])
def home():
    return jsonify({"mensagem": "API do sistema de notas fiscais rodando!"})

# Rota para listar notas fiscais
@app.route("/notas", methods=["GET"])
def listar_notas():
    try:
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notas_fiscais")
        notas = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(notas)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar notas fiscais: {str(e)}"}), 500

# Rota para cadastrar usuários
@app.route("/usuarios", methods=["POST"])
def cadastrar_usuario():
    dados = request.json
    nome = dados.get("nome")
    cpf = dados.get("cpf")
    senha = dados.get("senha")
    tipo = dados.get("tipo")  # 'admin' ou 'motorista'

    if not nome or not cpf or not senha or not tipo:
        return jsonify({"erro": "Todos os campos são obrigatórios."}), 400

    senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
    
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        sql = """
        INSERT INTO usuarios (nome, cpf, senha, tipo)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (nome, cpf, senha_hash, tipo))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"mensagem": "Usuário cadastrado com sucesso!"})
    except Exception as e:
        return jsonify({"erro": f"Erro ao cadastrar usuário: {str(e)}"}), 500

# Rota para listar usuários
@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    try:
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, cpf, tipo FROM usuarios")
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar usuários: {str(e)}"}), 500

# Rota para autenticação de usuário
@app.route("/login", methods=["POST"])
def login():
    dados = request.json
    cpf = dados.get("cpf")
    senha = dados.get("senha")
    
    conn = conectar_banco()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome, senha, tipo FROM usuarios WHERE cpf = %s", (cpf,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if usuario and bcrypt.check_password_hash(usuario["senha"], senha):
        return jsonify({"mensagem": "Login bem-sucedido!", "usuario": usuario})
    else:
        return jsonify({"erro": "CPF ou senha inválidos."}), 401

if __name__ == "__main__":
    app.run(debug=True)
