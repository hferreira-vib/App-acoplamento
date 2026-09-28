"""Calculos de engenharia: torque nominal, torque de projeto e fator de servico."""

# 1 CV (cavalo-vapor metrico) = 0.7355 kW (75 kgf.m/s).
CV_PARA_KW = 0.7355


def cv_para_kw(potencia_cv: float) -> float:
    """Converte potencia de CV (cavalo-vapor metrico) para kW."""
    return potencia_cv * CV_PARA_KW


def torque_nominal(potencia_kw: float, rpm: float) -> float:
    """Torque nominal em Nm.

    Formula: T [Nm] = (P [kW] * 9550) / n [rpm]

    A constante 9550 vem de 60000 / (2*pi), convertendo kW e rpm em Nm.
    """
    if rpm <= 0:
        raise ValueError("A rotacao (RPM) deve ser maior que zero.")
    if potencia_kw < 0:
        raise ValueError("A potencia (kW) nao pode ser negativa.")
    return (potencia_kw * 9550.0) / rpm


def torque_projeto(torque_nom: float, fator_servico: float) -> float:
    """Torque de projeto em Nm = Torque Nominal * Fator de Servico."""
    if fator_servico <= 0:
        raise ValueError("O fator de servico deve ser maior que zero.")
    return torque_nom * fator_servico

# A logica de Fator de Servico (matriz acionamento x maquina, regra de bancada)
# vive agora em logic/fator_servico.py. Este modulo cobre apenas os calculos de
# potencia/torque.
