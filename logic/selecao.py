"""Selecao e verificacao de acoplamentos a partir do catalogo."""

# Chaves do catalogo (mantidas centralizadas para evitar erros de digitacao).
K_CAT = "Categoria"
K_MOD = "Modelo"
K_TORQUE = "Torque Maximo (Nm)"
K_RPM = "Rotacao Maxima (RPM)"
K_FURO = "Furo Maximo (mm)"


def listar_categorias(catalogo: dict) -> list:
    """Lista as categorias unicas presentes no catalogo, em ordem de aparicao."""
    vistos = []
    for item in catalogo.get("acoplamentos", []):
        if item[K_CAT] not in vistos:
            vistos.append(item[K_CAT])
    return vistos


def listar_modelos(catalogo: dict, categoria: str) -> list:
    """Lista os modelos de uma categoria, ordenados por torque crescente."""
    itens = [i for i in catalogo.get("acoplamentos", []) if i[K_CAT] == categoria]
    itens.sort(key=lambda x: x[K_TORQUE])
    return [i[K_MOD] for i in itens]


def obter_modelo(catalogo: dict, categoria: str, modelo: str) -> dict | None:
    """Devolve o dict de um modelo especifico do catalogo."""
    for item in catalogo.get("acoplamentos", []):
        if item[K_CAT] == categoria and item[K_MOD] == modelo:
            return item
    return None


def sugerir_acoplamento(
    catalogo: dict,
    torque_projeto: float,
    furo_motor: float,
    furo_movido: float,
    rpm: float,
    categoria: str | None = None,
) -> dict:
    """Modo 1 - Sugestao Automatica.

    Filtra o catalogo (opcionalmente por categoria) e devolve o menor modelo
    (menor torque maximo) que satisfaz TODOS os criterios:
      - Torque Maximo  >= Torque de Projeto
      - Furo Maximo    >= maior dos dois diametros de veio
      - Rotacao Maxima >= RPM de trabalho

    Retorna dict: {encontrado: bool, modelo: dict|None, candidatos: list}
    """
    furo_requerido = max(furo_motor, furo_movido)

    universo = catalogo.get("acoplamentos", [])
    if categoria and categoria != "Todas":
        universo = [i for i in universo if i[K_CAT] == categoria]

    # Ordena por torque crescente para garantir "o menor que atende".
    universo = sorted(universo, key=lambda x: x[K_TORQUE])

    aprovados = [
        item
        for item in universo
        if item[K_TORQUE] >= torque_projeto
        and item[K_FURO] >= furo_requerido
        and item[K_RPM] >= rpm
    ]

    if aprovados:
        return {"encontrado": True, "modelo": aprovados[0], "candidatos": aprovados}
    return {"encontrado": False, "modelo": None, "candidatos": []}


def verificar_modelo(
    modelo: dict,
    torque_projeto: float,
    furo_motor: float,
    furo_movido: float,
    rpm: float,
) -> dict:
    """Modo 2 - Verificacao de Modelo Especifico.

    Cruza os dados do modelo escolhido com os dados calculados e devolve um
    parecer tecnico. Retorna dict: {aprovado: bool, motivos: list[str]}.
    """
    motivos = []

    # Criterio 1: Torque
    if modelo[K_TORQUE] < torque_projeto:
        motivos.append(
            f"Torque de projeto ({torque_projeto:.1f} Nm) excede o torque maximo "
            f"do acoplamento ({modelo[K_TORQUE]} Nm)."
        )

    # Criterio 2: Furo do eixo motor
    if furo_motor > modelo[K_FURO]:
        motivos.append(
            f"Furo do eixo motor ({furo_motor:.0f}mm) excede o furo maximo "
            f"do cubo ({modelo[K_FURO]}mm)."
        )

    # Criterio 3: Furo do eixo movido
    if furo_movido > modelo[K_FURO]:
        motivos.append(
            f"Furo do eixo movido ({furo_movido:.0f}mm) excede o furo maximo "
            f"do cubo ({modelo[K_FURO]}mm)."
        )

    # Criterio 4: Rotacao
    if rpm > modelo[K_RPM]:
        motivos.append(
            f"Rotacao de trabalho ({rpm:.0f} RPM) excede a rotacao maxima "
            f"do acoplamento ({modelo[K_RPM]} RPM)."
        )

    return {"aprovado": len(motivos) == 0, "motivos": motivos}
