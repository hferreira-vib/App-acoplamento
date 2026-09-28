"""
Expande o catalogo de acoplamentos com linhas do mercado brasileiro.
================================================================

Adiciona novas categorias/modelos ao data/catalogo_acoplamentos.json SEM
alterar ou remover o que ja existe. E idempotente: rodar varias vezes nao
duplica itens (a chave unica e Categoria + Modelo).

Chaves respeitadas (identicas as do app, para nao quebrar a aplicacao):
  Categoria, Modelo, Torque Maximo (Nm), Rotacao Maxima (RPM), Furo Maximo (mm)
  + Peso (kg), Momento de Inercia (kg.m2) e desalinhamentos (para a ficha tecnica).

Dados tecnicos sao estimativas realistas de mercado por escalonamento de
tamanho/tecnologia - confirmar sempre no datasheet oficial do fabricante.

Executar:  python scripts/expandir_catalogo.py
"""

import json
from pathlib import Path

CATALOGO = Path(__file__).resolve().parent.parent / "data" / "catalogo_acoplamentos.json"


def item(categoria, modelo, torque, rpm, furo, peso, inercia, ang, rad, ax):
    """Monta um registo do catalogo com as chaves exatas usadas pela app."""
    return {
        "Categoria": categoria,
        "Modelo": modelo,
        "Torque Maximo (Nm)": torque,
        "Rotacao Maxima (RPM)": rpm,
        "Furo Maximo (mm)": furo,
        "Peso (kg)": peso,
        "Momento de Inercia (kg.m2)": inercia,
        "Desalinhamento Angular (graus)": ang,
        "Desalinhamento Radial (mm)": rad,
        "Desalinhamento Axial (mm)": ax,
    }


# ---------------------------------------------------------------------------
# 1. Acoplamento Hidraulico (HDA / Voith) - acionamento de correias e moinhos.
#    Enchimento constante; torque cresce com o tamanho, rpm cai com o tamanho.
# ---------------------------------------------------------------------------
CAT_HIDRAULICO = "Acoplamento Hidraulico (HDA / Voith)"
hidraulicos = [
    item(CAT_HIDRAULICO, "HDA 274", 320, 4000, 60, 9.0, 0.02, 0.5, 0.3, 2.0),
    item(CAT_HIDRAULICO, "HDA 366", 780, 3600, 80, 18.0, 0.06, 0.5, 0.3, 2.0),
    item(CAT_HIDRAULICO, "HDA 422", 1500, 3300, 95, 30.0, 0.15, 0.5, 0.3, 2.0),
    item(CAT_HIDRAULICO, "HDA 480", 2600, 2900, 110, 48.0, 0.32, 0.5, 0.3, 2.0),
    item(CAT_HIDRAULICO, "HDA 562", 4800, 2500, 130, 82.0, 0.75, 0.5, 0.3, 2.0),
    item(CAT_HIDRAULICO, "HDA 750", 11000, 1800, 170, 190.0, 3.20, 0.5, 0.3, 2.0),
]

# ---------------------------------------------------------------------------
# 2. Garras - Linha nacional HDA (HA). Elastomero em garras, tipo Rotex/Lovejoy.
# ---------------------------------------------------------------------------
CAT_GARRAS_HA = "Garras (HDA Linha HA)"
garras_ha = [
    item(CAT_GARRAS_HA, "HA-40", 35, 8000, 28, 0.5, 0.0001, 1.0, 0.3, 1.4),
    item(CAT_GARRAS_HA, "HA-55", 120, 6500, 38, 1.3, 0.0004, 1.0, 0.3, 1.4),
    item(CAT_GARRAS_HA, "HA-70", 265, 5000, 48, 2.6, 0.0011, 1.0, 0.3, 1.4),
    item(CAT_GARRAS_HA, "HA-90", 520, 4000, 62, 5.0, 0.003, 1.0, 0.3, 1.4),
    item(CAT_GARRAS_HA, "HA-110", 950, 3200, 80, 9.5, 0.0085, 1.0, 0.3, 1.4),
    item(CAT_GARRAS_HA, "HA-130", 1700, 2700, 95, 16.0, 0.019, 1.0, 0.3, 1.4),
]

# ---------------------------------------------------------------------------
# 4. Elastomero Bipartido (Rexnord Viva) - elemento fendido, montagem/troca facil.
# ---------------------------------------------------------------------------
CAT_VIVA = "Elastomero Bipartido (Rexnord Viva)"
viva = [
    item(CAT_VIVA, "V110", 90, 4500, 42, 2.2, 0.0008, 1.0, 0.5, 1.5),
    item(CAT_VIVA, "V130", 170, 4000, 48, 3.2, 0.0015, 1.0, 0.5, 1.5),
    item(CAT_VIVA, "V150", 310, 3600, 55, 4.8, 0.003, 1.0, 0.5, 1.5),
    item(CAT_VIVA, "V170", 530, 3100, 62, 6.8, 0.006, 1.0, 0.5, 1.5),
    item(CAT_VIVA, "V190", 850, 2800, 70, 9.5, 0.011, 1.0, 0.5, 1.5),
    item(CAT_VIVA, "V210", 1300, 2500, 80, 13.0, 0.02, 1.0, 0.5, 1.5),
    item(CAT_VIVA, "V245", 2100, 2100, 95, 21.0, 0.045, 1.0, 0.5, 1.5),
    item(CAT_VIVA, "V290", 3600, 1800, 110, 34.0, 0.095, 1.0, 0.5, 1.5),
]

# ---------------------------------------------------------------------------
# 5. Laminas/Disco (Rexnord Thomas Disc) - Serie 54/71. Alta rotacao, precisao.
# ---------------------------------------------------------------------------
CAT_THOMAS = "Laminas/Disco (Rexnord Thomas Disc)"
thomas = [
    item(CAT_THOMAS, "THOMAS 110", 280, 12000, 45, 6.5, 0.005, 0.5, 0.15, 1.5),
    item(CAT_THOMAS, "THOMAS 162", 680, 9000, 60, 13.0, 0.018, 0.5, 0.15, 1.5),
    item(CAT_THOMAS, "THOMAS 200", 1350, 7500, 75, 24.0, 0.055, 0.5, 0.15, 1.5),
    item(CAT_THOMAS, "THOMAS 225", 2100, 6700, 85, 34.0, 0.11, 0.5, 0.15, 1.5),
    item(CAT_THOMAS, "THOMAS 262", 3600, 5800, 100, 52.0, 0.24, 0.5, 0.15, 1.5),
    item(CAT_THOMAS, "THOMAS 312", 6200, 4900, 120, 82.0, 0.55, 0.5, 0.15, 1.5),
    item(CAT_THOMAS, "THOMAS 350", 9500, 4300, 140, 120.0, 1.05, 0.5, 0.15, 1.5),
]

# Nota: a linha "Elastomero PU (FALK Wrapflex)" (5R..80R) ja existe no catalogo,
# portanto NAO e adicionada aqui para evitar duplicados.
NOVOS_ITENS = hidraulicos + garras_ha + viva + thomas


def main():
    with open(CATALOGO, "r", encoding="utf-8") as f:
        dados = json.load(f)

    existentes = dados.setdefault("acoplamentos", [])
    ja_no_catalogo = {(i["Categoria"], i["Modelo"]) for i in existentes}

    adicionados = 0
    for novo in NOVOS_ITENS:
        chave = (novo["Categoria"], novo["Modelo"])
        if chave in ja_no_catalogo:
            print(f"  - ja existe, ignorado: {chave[0]} / {chave[1]}")
            continue
        existentes.append(novo)
        ja_no_catalogo.add(chave)
        adicionados += 1

    with open(CATALOGO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\nConcluido. {adicionados} novo(s) item(ns) adicionado(s).")
    print(f"Total de acoplamentos no catalogo: {len(existentes)}.")


if __name__ == "__main__":
    main()
