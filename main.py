import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret_key'

# Configurando logging
logging.basicConfig(level=logging.INFO)

# Função para criar o banco de dados e as tabelas
def criar_banco_de_dados():
    try:
        conn = sqlite3.connect('urna_eletronica.db')
        cursor = conn.cursor()

        # Criação da tabela de candidatos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL
            )
        ''')

        # Criação da tabela de votos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidato_id INTEGER NOT NULL,
                preferencia INTEGER NOT NULL,
                FOREIGN KEY (candidato_id) REFERENCES candidatos(id)
            )
        ''')

        conn.commit()
        conn.close()
        logging.info("Banco de dados criado com sucesso.")
    except sqlite3.Error as e:
        logging.error(f"Erro ao criar banco de dados: {e}")

# Função para obter conexão com o banco de dados
def get_db_connection():
    try:
        conn = sqlite3.connect('urna_eletronica.db')
        return conn
    except sqlite3.Error as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Página inicial
@app.route('/')
def index():
    logging.info("Página inicial acessada")
    return render_template('index.html')

# Página de cadastro de candidatos
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500

    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        if nome:
            cursor.execute('INSERT INTO candidatos (nome) VALUES (?)', (nome,))
            conn.commit()
            flash('Candidato cadastrado com sucesso!', 'success')
        else:
            flash('Nome do candidato não pode ser vazio.', 'danger')

    # Exibir todos os candidatos cadastrados
    cursor.execute('SELECT * FROM candidatos')
    candidatos = cursor.fetchall()

    conn.close()
    return render_template('cadastrar.html', candidatos=candidatos)

# Rota para excluir um candidato
@app.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500

    cursor = conn.cursor()

    # Excluir o candidato
    cursor.execute('DELETE FROM candidatos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Candidato excluído com sucesso!', 'success')
    return redirect(url_for('cadastrar'))

# Rota para renomear um candidato
@app.route('/renomear/<int:id>', methods=['POST'])
def renomear(id):
    novo_nome = request.form['novo_nome']
    if novo_nome:
        conn = get_db_connection()
        if conn is None:
            return "Erro ao conectar ao banco de dados.", 500

        cursor = conn.cursor()

        # Renomear o candidato
        cursor.execute('UPDATE candidatos SET nome = ? WHERE id = ?', (novo_nome, id))
        conn.commit()
        conn.close()
        flash('Candidato renomeado com sucesso!', 'success')
    else:
        flash('O nome do candidato não pode ser vazio.', 'danger')
    return redirect(url_for('cadastrar'))

# Página de votação
@app.route('/votar', methods=['GET', 'POST'])
def votar():
    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidatos")
    candidatos = cursor.fetchall()

    if request.method == 'POST':
        preferencias = request.form.getlist('preferencia')
        if preferencias:
            for i, candidato_id in enumerate(preferencias):
                cursor.execute('INSERT INTO votos (candidato_id, preferencia) VALUES (?, ?)', (candidato_id, i + 1))
            conn.commit()
            flash('Votos computados com sucesso!', 'success')
            return redirect(url_for('resultado'))

    conn.close()
    return render_template('votar.html', candidatos=candidatos)

# Página de resultados
@app.route('/resultado')
def resultado():
    conn = get_db_connection()
    if conn is None:
        return "Erro ao conectar ao banco de dados.", 500

    cursor = conn.cursor()

    # Obter o total de candidatos
    cursor.execute('SELECT COUNT(*) FROM candidatos')
    num_candidatos = cursor.fetchone()[0]

    # Cálculo do Total de Pontos Máximo (TPM)
    tpm = 6 * num_candidatos

    # Obter o número de votos por candidato e calcular o total de pontos
    cursor.execute('''
        SELECT candidatos.nome, SUM(6 - (votos.preferencia - 1)) AS total_pontos
        FROM votos
        JOIN candidatos ON votos.candidato_id = candidatos.id
        GROUP BY candidatos.id
        ORDER BY total_pontos DESC
    ''')
    resultados = cursor.fetchall()

    # Calcular a porcentagem (RF%) para cada candidato
    resultados_com_porcentagem = [
        (resultado[0], resultado[1], (resultado[1] / tpm) * 100 if tpm > 0 else 0)
        for resultado in resultados
    ]

    conn.close()
    return render_template('resultado.html', resultados=resultados_com_porcentagem, tpm=tpm)

# Inicialização do servidor Flask
if __name__ == '__main__':
    criar_banco_de_dados()  # Recriar o banco de dados ao iniciar o servidor
    port = int(os.environ.get('PORT', 5000))  # Captura a porta configurada pelo ambiente
    app.run(host='0.0.0.0', port=port)  # Executa o servidor Flask na porta correta
