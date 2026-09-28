"""Fator de Servico (FS): selecao de acionamento x maquina movida.

Fonte de dados: data/fator_servico.json (matriz FS por Tipo de Acionamento x
Maquina Movida, base AGMA/DIN / Falk Steelflex T10).

Regra especial de bancada/ensaio: as maquinas listadas em `MAQUINAS_BANCADA`
(motor eletrico em bancada/gerador/back-to-back e mancais/eixos de suporte) sao
elementos de transmissao praticamente uniformes. Independentemente do tipo de
acionamento, usam um FS base limpo (`FS_BANCADA`), tipico de ensaio continuo.
"""

# FS base limpo para montagens de bancada/ensaio (faixa tipica 1.0 a 1.25).
FS_BANCADA = 1.0

# Maquinas que sempre usam o FS base limpo (independente do acionamento).
MAQUINAS_BANCADA = frozenset({
    "Motor Elétrico (Bancada / Gerador / Back-to-Back)",
    "Mancal / Eixo de Suporte",
})


def listar_acionamentos(dados_fs: dict) -> list:
    """Lista os tipos de acionamento disponiveis (ordem do JSON)."""
    return list(dados_fs.get("matriz", {}).keys())


def listar_maquinas(dados_fs: dict, acionamento: str) -> list:
    """Lista as maquinas movidas disponiveis para um dado acionamento."""
    return list(dados_fs.get("matriz", {}).get(acionamento, {}).keys())


def is_bancada(maquina: str) -> bool:
    """Indica se a maquina movida usa o FS base limpo de bancada/ensaio."""
    return maquina in MAQUINAS_BANCADA


def get_fator_servico(dados_fs: dict, acionamento: str, maquina: str) -> float:
    """Devolve o FS cruzando acionamento x maquina movida.

    Aplica a regra de bancada: se a maquina movida for de bancada/suporte,
    retorna `FS_BANCADA` (base limpo) independentemente do acionamento.
    Caso contrario, cruza na matriz do `dados_fs`.
    """
    if is_bancada(maquina):
        return FS_BANCADA

    matriz = dados_fs.get("matriz", {})
    try:
        return float(matriz[acionamento][maquina])
    except KeyError:
        raise KeyError(
            f"Fator de servico nao encontrado para '{acionamento}' x '{maquina}'."
        )
