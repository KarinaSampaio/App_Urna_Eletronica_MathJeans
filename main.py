from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "chave-secreta"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eleicoes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo para o banco de dados
class Eleitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    titulo = db.Column(db.String(20), unique=True, nullable=False)

class Candidato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

class Voto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eleitor_id = db.Column(db.Integer, db.ForeignKey('eleitor.id'), nullable=False)
    candidato_id = db.Column(db.Integer, db.ForeignKey('candidato.id'), nullable=False)
    preferencia = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

    # Inserir candidatos automaticamente se não existirem
    if Candidato.query.count() == 0:
        candidatos_iniciais = ['Ronaldo', 'Filipe', 'Paulo', 'Ester', 'Nathália']
        for nome in candidatos_iniciais:
            novo_candidato = Candidato(nome=nome)
            db.session.add(novo_candidato)
        db.session.commit()

@app.route('/')
def index():
    """Página inicial com opções para cadastro de eleitor, votação e resultados."""
    return render_template('index.html')

@app.route('/cadastrar_eleitor', methods=['GET', 'POST'])
def cadastrar_eleitor():
    """Página de cadastro de eleitor e redirecionamento para a votação."""
    if request.method == 'POST':
        nome = request.form['nome']
        titulo_eleitor = request.form['titulo_eleitor']

        # Verifica se os campos estão preenchidos
        if not nome or not titulo_eleitor:
            flash("Todos os campos são obrigatórios!", "danger")
            return redirect(url_for('cadastrar_eleitor'))

        # Verifica se o eleitor já foi cadastrado
        eleitor_existente = Eleitor.query.filter_by(titulo=titulo_eleitor).first()
        if eleitor_existente:
            flash("Este eleitor já foi cadastrado.", "danger")
            return redirect(url_for('cadastrar_eleitor'))

        # Cadastra o eleitor
        novo_eleitor = Eleitor(nome=nome, titulo=titulo_eleitor)
        db.session.add(novo_eleitor)
        db.session.commit()

        # Armazena o ID do eleitor na sessão
        session['eleitor_id'] = novo_eleitor.id

        flash("Eleitor cadastrado com sucesso!", "success")

        # Redireciona para a página de votação
        return redirect(url_for('votar'))

    return render_template('pagina_inicial.html')

@app.route('/cadastrar_candidato', methods=['GET', 'POST'])
def cadastrar_candidato():
    """Página de cadastro de candidatos."""
    if request.method == 'POST':
        nome_candidato = request.form['nome_candidato']

        # Verifica se o candidato já existe
        candidato_existente = Candidato.query.filter_by(nome=nome_candidato).first()
        if candidato_existente:
            flash("Candidato já cadastrado!", "danger")
            return redirect(url_for('cadastrar_candidato'))

        # Cadastra o candidato
        novo_candidato = Candidato(nome=nome_candidato)
        db.session.add(novo_candidato)
        db.session.commit()
        flash("Candidato cadastrado com sucesso!", "success")
        return redirect(url_for('cadastrar_candidato'))

    candidatos = Candidato.query.all()
    return render_template('cadastrar.html', candidatos=candidatos)

@app.route('/votar', methods=['GET', 'POST'])
def votar():
    """Página de votação onde o eleitor vota e, em seguida, é redirecionado para a página de agradecimento."""
    candidatos = Candidato.query.all()
    eleitor_id = session.get('eleitor_id')  # Recupera o ID do eleitor da sessão

    if not eleitor_id:
        flash("Você precisa se cadastrar antes de votar.", "danger")
        return redirect(url_for('cadastrar_eleitor'))

    if request.method == 'POST':
        preferencias = request.form.getlist('preferencia')

        # Registrar os votos de acordo com as preferências
        for i, candidato_id in enumerate(preferencias):
            voto = Voto(eleitor_id=eleitor_id, candidato_id=candidato_id, preferencia=i + 1)
            db.session.add(voto)
            db.session.commit()

        flash("Voto registrado com sucesso!", "success")
        return redirect(url_for('agradecimento'))  # Redirecionar para a página de agradecimento

    return render_template('votar.html', candidatos=candidatos)

@app.route('/agradecimento')
def agradecimento():
    """Página de agradecimento após a votação."""
    return render_template('agradecimento.html')

@app.route('/resultado')
def resultado():
    """Exibe o resultado tradicional da votação."""
    resultados = calcular_resultados()
    return render_template('resultado.html', resultados=resultados)

@app.route('/resultado_minimax')
def resultado_minimax():
    """Exibe o resultado minimax da votação."""
    resultados = calcular_minimax()
    return render_template('resultado_minimax.html', resultados=resultados)

@app.route('/resetar_bd', methods=['POST'])
def resetar_bd():
    """Reseta o banco de dados, excluindo todos os eleitores e votos."""
    db.drop_all()
    db.create_all()
    flash("Banco de dados resetado com sucesso!", "success")
    return redirect(url_for('index'))

def calcular_resultados():
    """Calcula o resultado tradicional com base nos votos."""
    total_pontos = defaultdict(int)

    votos = Voto.query.all()
    for voto in votos:
        total_pontos[voto.candidato_id] += 4 - voto.preferencia

    total = sum(total_pontos.values())
    resultados = [(Candidato.query.get(candidato_id).nome, pontos, (pontos / total) * 100 if total > 0 else 0)
                  for candidato_id, pontos in total_pontos.items()]

    return sorted(resultados, key=lambda x: -x[1])  # Ordena os resultados por pontos

def calcular_minimax():
    """Calcula o resultado minimax com a fórmula voto/n * 100."""
    total_pontos = defaultdict(list)

    votos = Voto.query.all()
    for voto in votos:
        percentagem = (4 - voto.preferencia) / 4 * 100
        total_pontos[voto.candidato_id].append(percentagem)

    resultados = [(Candidato.query.get(candidato_id).nome, sum(pontos), sum(pontos) / len(pontos) if pontos else 0)
                  for candidato_id, pontos in total_pontos.items()]

    return sorted(resultados, key=lambda x: -x[1])  # Ordena os resultados por pontuação

if __name__ == '__main__':
    app.run(debug=True)
