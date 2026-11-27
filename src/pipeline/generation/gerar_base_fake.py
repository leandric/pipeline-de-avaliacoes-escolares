"""Gera uma base fake de avaliações escolares em CSV.

Cada linha é uma prova de um aluno em uma disciplina. Uma prova é definida por
(série, disciplina, versão): todos os alunos que fizeram a mesma prova
compartilham o mesmo gabarito e os mesmos pesos.

Uso:
    uv run python src/pipeline/generation/gerar_base_fake.py
"""

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

RAIZ = Path(__file__).resolve().parents[3]
SAIDA_PADRAO = RAIZ / "data" / "base_fake_avaliacoes.csv"

ANO_LETIVO = 2026
N_QUESTOES = 50
ALTERNATIVAS = "ABCDE"
VERSOES = "ABCD"
ALUNOS_POR_TURMA = (30, 40)
UNIDADES_PESO = 10_000  # pesos com 4 casas decimais, somando exatamente 1
PROB_BRANCO = 0.03
PROB_INVALIDA = 0.02  # mais de uma alternativa marcada
RESPOSTA_BRANCO = " "
RESPOSTA_INVALIDA = "*"

ESCOLAS = ["Unidade Centro", "Unidade Norte", "Unidade Sul"]
PERIODOS = ["Manhã", "Tarde", "Integral"]

SERIES = [
    ("Fundamental", "6º ano", "EF6"),
    ("Fundamental", "7º ano", "EF7"),
    ("Fundamental", "8º ano", "EF8"),
    ("Fundamental", "9º ano", "EF9"),
    ("Médio", "1ª série", "EM1"),
    ("Médio", "2ª série", "EM2"),
    ("Médio", "3ª série", "EM3"),
]

# (nome, código)
DISCIPLINAS = {
    "Fundamental": [
        ("Português", "POR"),
        ("Matemática", "MAT"),
        ("Ciências", "CIE"),
        ("História", "HIS"),
        ("Geografia", "GEO"),
        ("Inglês", "ING"),
    ],
    "Médio": [
        ("Português", "POR"),
        ("Matemática", "MAT"),
        ("Física", "FIS"),
        ("Química", "QUI"),
        ("Biologia", "BIO"),
        ("História", "HIS"),
        ("Geografia", "GEO"),
        ("Inglês", "ING"),
    ],
}

COLUNAS = [
    "ra",
    "nome",
    "escola",
    "ano_letivo",
    "segmento",
    "serie",
    "turma",
    "periodo",
    "disciplina",
    "data_prova",
    "versao",
    "id_prova",
    "respostas",
    "gabarito",
    "pesos_perguntas",
]


@dataclass(frozen=True)
class Prova:
    id_prova: str
    data_prova: date
    gabarito: str
    pesos: str
    dificuldades: tuple[float, ...]


def gerar_pesos(rng: random.Random) -> str:
    """Pesos das questões com 4 casas decimais, somando exatamente 1."""
    brutos = [rng.uniform(0.5, 2.0) for _ in range(N_QUESTOES)]
    total = sum(brutos)
    exatos = [b / total * UNIDADES_PESO for b in brutos]
    unidades = [int(e) for e in exatos]
    faltam = UNIDADES_PESO - sum(unidades)
    por_resto = sorted(range(N_QUESTOES), key=lambda i: exatos[i] - unidades[i], reverse=True)
    for i in por_resto[:faltam]:
        unidades[i] += 1
    return ",".join(f"{u / UNIDADES_PESO:.4f}" for u in unidades)


class Gerador:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        Faker.seed(seed)
        self.faker = Faker("pt_BR")
        self.provas: dict[tuple[str, str, str], Prova] = {}
        self.datas: dict[tuple[str, str], date] = {}
        self.ras: set[str] = set()

    def prova(self, serie_cod: str, disc_cod: str, versao: str) -> Prova:
        chave = (serie_cod, disc_cod, versao)
        if chave not in self.provas:
            data = self.datas.setdefault(
                (serie_cod, disc_cod),
                date(ANO_LETIVO, 3, 1) + timedelta(days=self.rng.randint(0, 120)),
            )
            self.provas[chave] = Prova(
                id_prova=f"{serie_cod}-{disc_cod}-{versao}",
                data_prova=data,
                gabarito="".join(self.rng.choice(ALTERNATIVAS) for _ in range(N_QUESTOES)),
                pesos=gerar_pesos(self.rng),
                dificuldades=tuple(self.rng.uniform(0.2, 0.8) for _ in range(N_QUESTOES)),
            )
        return self.provas[chave]

    def novo_ra(self) -> str:
        while True:
            ra = str(self.rng.randint(10_000_000, 99_999_999))
            if ra not in self.ras:
                self.ras.add(ra)
                return ra

    def nome(self) -> str:
        return f"{self.faker.first_name()} {self.faker.last_name()} {self.faker.last_name()}"

    def responder(self, prova: Prova, habilidade: float) -> str:
        respostas = []
        for certa, dificuldade in zip(prova.gabarito, prova.dificuldades):
            sorteio = self.rng.random()
            if sorteio < PROB_INVALIDA:
                respostas.append(RESPOSTA_INVALIDA)
            elif sorteio < PROB_INVALIDA + PROB_BRANCO:
                respostas.append(RESPOSTA_BRANCO)
            else:
                p_acerto = min(0.98, max(0.05, habilidade + (dificuldade - 0.5) * 0.4))
                if self.rng.random() < p_acerto:
                    respostas.append(certa)
                else:
                    respostas.append(self.rng.choice(ALTERNATIVAS.replace(certa, "")))
        return "".join(respostas)

    def turmas(self):
        """Gera combinações (escola, série, turma) sem repetição, indefinidamente."""
        rodada = 0
        while True:
            nome_turma = chr(ord("A") + rodada % 26) + (str(rodada // 26) if rodada >= 26 else "")
            combinacoes = [(escola, serie) for escola in ESCOLAS for serie in SERIES]
            self.rng.shuffle(combinacoes)
            for escola, serie in combinacoes:
                yield escola, serie, nome_turma
            rodada += 1

    def linhas_da_turma(self, escola: str, serie: tuple[str, str, str], turma: str):
        segmento, serie_nome, serie_cod = serie
        periodo = self.rng.choice(PERIODOS)
        disciplinas = DISCIPLINAS[segmento]
        n_alunos = self.rng.randint(*ALUNOS_POR_TURMA)
        alunos = [(self.novo_ra(), self.nome(), self.rng.betavariate(5, 3)) for _ in range(n_alunos)]

        # versões distribuídas de forma equilibrada dentro da turma, por disciplina
        versoes_por_disciplina = {}
        for _, disc_cod in disciplinas:
            versoes = [VERSOES[i % len(VERSOES)] for i in range(n_alunos)]
            self.rng.shuffle(versoes)
            versoes_por_disciplina[disc_cod] = versoes

        for i, (ra, nome, habilidade) in enumerate(alunos):
            for disc_nome, disc_cod in disciplinas:
                versao = versoes_por_disciplina[disc_cod][i]
                prova = self.prova(serie_cod, disc_cod, versao)
                nivel = min(1.0, max(0.0, habilidade + self.rng.gauss(0, 0.08)))
                yield {
                    "ra": ra,
                    "nome": nome,
                    "escola": escola,
                    "ano_letivo": ANO_LETIVO,
                    "segmento": segmento,
                    "serie": serie_nome,
                    "turma": turma,
                    "periodo": periodo,
                    "disciplina": disc_nome,
                    "data_prova": prova.data_prova.isoformat(),
                    "versao": versao,
                    "id_prova": prova.id_prova,
                    "respostas": self.responder(prova, nivel),
                    "gabarito": prova.gabarito,
                    "pesos_perguntas": prova.pesos,
                }

    def gerar(self, n_registros: int) -> list[dict]:
        linhas: list[dict] = []
        for escola, serie, turma in self.turmas():
            linhas.extend(self.linhas_da_turma(escola, serie, turma))
            if len(linhas) >= n_registros:
                return linhas[:n_registros]


def perguntar_quantidade() -> int:
    while True:
        entrada = input("Quantos registros deseja gerar? ").strip()
        if entrada.isdigit() and int(entrada) > 0:
            return int(entrada)
        print("Informe um número inteiro maior que zero.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=42, help="semente para gerar sempre a mesma base")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="caminho do CSV de saída")
    args = parser.parse_args()

    n_registros = perguntar_quantidade()
    linhas = Gerador(args.seed).gerar(n_registros)

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    # QUOTE_ALL preserva os espaços em branco das respostas e as vírgulas dos pesos
    with args.saida.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS, quoting=csv.QUOTE_ALL)
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"{len(linhas)} registros gerados em {args.saida}")


if __name__ == "__main__":
    main()
