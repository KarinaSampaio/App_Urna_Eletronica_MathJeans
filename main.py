from flask import Flask, render_template, request, redirect, url_for, flash
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "chave-secreta"

# Simulação de banco de dados em memória para eleitores, candidatos e votos
eleitores = []
candidatos = []
votos = defaultdict(list)  # Cada candidato terá uma lista com as contagens de votos em diferentes rodadas


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
        for eleitor in eleitores:
            if eleitor['titulo'] == titulo_eleitor:
                flash("Este eleitor já foi cadastrado.", "danger")
                return redirect(url_for('cadastrar_eleitor'))

        # Cadastra o eleitor
        eleitores.append({'nome': nome, 'titulo': titulo_eleitor})
        flash("Eleitor cadastrado com sucesso!", "success")

        # Redireciona para a página de votação
        return redirect(url_for('votar'))

    return render_template('pagina_inicial.html')


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """Página de cadastro de candidatos."""
    if request.method == 'POST':
        nome_candidato = request.form['nome_candidato']

        # Verifica se o candidato já existe
        for candidato in candidatos:
            if candidato == nome_candidato:
                flash("Candidato já cadastrado!", "danger")
                return redirect(url_for('cadastrar'))

        # Cadastra o candidato
        candidatos.append(nome_candidato)
        flash("Candidato cadastrado com sucesso!", "success")
        return redirect(url_for('cadastrar'))

    return render_template('cadastrar.html', candidatos=candidatos)


@app.route('/votar', methods=['GET', 'POST'])
def votar():
    """Página de votação onde o eleitor vota e, em seguida, é redirecionado para a página de agradecimento."""
    if request.method == 'POST':
        preferencias = request.form.getlist('preferencia')

        # Registrar os votos de acordo com as preferências
        for i, candidato_id in enumerate(preferencias):
            votos[int(candidato_id)].append(i + 1)  # i+1 define a ordem de preferência

        flash("Voto registrado com sucesso!", "success")
        return redirect(url_for('agradecimento'))  # Redirecionar para a página de agradecimento

    return render_template('votar.html', candidatos=enumerate(candidatos))


@app.route('/agradecimento')
def agradecimento():
    """Página de agradecimento após a votação."""
    return render_template('agradecimento.html')


@app.route('/resultado')
def resultado():
    """Exibe o resultado tradicional da votação."""
    resultados = calcular_resultados(votos)

    # Se não houver candidatos, adicionamos uma mensagem de aviso
    if not candidatos:
        flash("Nenhum candidato cadastrado ainda.", "danger")
        return render_template('resultado.html', resultados=[], votos_registrados=False)

    # Exibe a página de resultados mesmo que não haja votos
    return render_template('resultado.html', resultados=resultados, votos_registrados=bool(votos))


@app.route('/resultado_minimax')
def resultado_minimax():
    """Exibe o resultado minimax da votação."""
    total_eleitores = len(eleitores)  # Calcula o total de eleitores
    resultados = calcular_minimax(votos)

    # Se não houver candidatos, adicionamos uma mensagem de aviso
    if not candidatos:
        flash("Nenhum candidato cadastrado ainda.", "danger")
        return render_template('resultado_minimax.html', resultados=[], total_eleitores=total_eleitores,
                               votos_registrados=False)

    # Exibe a página de resultados mesmo que não haja votos
    return render_template('resultado_minimax.html', resultados=resultados, total_eleitores=total_eleitores,
                           votos_registrados=bool(votos))


@app.route('/resetar_bd', methods=['POST'])
def resetar_bd():
    """Reseta o banco de dados, excluindo todos os eleitores e votos."""
    global eleitores, candidatos, votos
    eleitores = []
    candidatos = []
    votos = defaultdict(list)
    flash("Banco de dados resetado com sucesso!", "success")
    return redirect(url_for('index'))


def calcular_resultados(votos):
    """Calcula o resultado tradicional com base nos votos."""
    total_pontos = defaultdict(int)

    for candidato_id, candidato_votos in votos.items():
        total_pontos[candidato_id] = sum(candidato_votos)

    total = sum(total_pontos.values())
    if total == 0:
        # Retorna uma lista com todos os candidatos, mas com pontuação 0
        return [(candidatos[candidato_id], 0, 0) for candidato_id in range(len(candidatos))]

    resultados = [(candidatos[candidato_id], pontos, (pontos / total) * 100 if total > 0 else 0)
                  for candidato_id, pontos in total_pontos.items()]

    return sorted(resultados, key=lambda x: -x[1])  # Ordena os resultados por pontos


def calcular_minimax(votos):
    """Calcula o resultado minimax com a fórmula voto/n * 100."""
    total_pontos = defaultdict(list)

    for candidato_id, candidato_votos in votos.items():
        for i, voto in enumerate(candidato_votos):
            percentagem = (voto / (i + 1)) * 100  # Fórmula ajustada
            total_pontos[candidato_id].append(percentagem)

    if not total_pontos:
        # Retorna uma lista com todos os candidatos, mas com pontuação 0
        return [(candidatos[candidato_id], 0, 0) for candidato_id in range(len(candidatos))]

    resultados = [(candidatos[candidato_id], sum(pontos), sum(pontos) / len(pontos) if pontos else 0)
                  for candidato_id, pontos in total_pontos.items()]

    return sorted(resultados, key=lambda x: -x[1])  # Ordena os resultados por pontuação


if __name__ == '__main__':
    app.run(debug=True)
