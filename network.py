"""
Bug Dupla 2 — "O Empate Impossível"
=====================================
Node-A e Node-B enviam o mesmo valor quase simultaneamente.
Como ambos usam relógios físicos locais independentes,
os timestamps chegam invertidos dependendo da ordem de rede.

Resultado: ao consultar o log, metade das execuções declara
Node-A vencedor; a outra metade declara Node-B.
O sistema é não-determinístico sem que ninguém perceba.

O erro parece ser um "bug de desempate" ou "condição de corrida",
mas a raiz é que não há forma de estabelecer ordem total
entre eventos concorrentes sem um mecanismo de relógio lógico.

Pista para o aluno: dois eventos simultâneos em nós diferentes
— qual realmente "veio primeiro"?
"""

import time
import random


# valor do lance empatado (injetado nos dois nós)
TIE_VALUE = 500.0
_tie_count = 0


def on_startup(node_id: str, clock: int) -> int:
    return clock


def on_get_timestamp(clock: int) -> int:
    """Substitui o relógio lógico por relógio físico (fonte do bug)."""
    # usa float de alta resolução para simular relógio físico real
    return time.time()


def on_send_bid(payload: dict) -> dict:
    """Força Node-A e Node-B a enviarem o mesmo valor de lance."""
    global _tie_count
    if payload["node_id"] in ("Node-A", "Node-B"):
        payload["value"] = TIE_VALUE
        _tie_count += 1
    return payload


def on_network_delay(base_delay: float) -> float:
    """Inverte propositalmente a ordem de chegada entre Node-A e Node-B."""
    # Node-A chega rápido, Node-B chega devagar → mas timestamps físicos
    # podem dizer o contrário dependendo dos relógios locais
    return base_delay + random.uniform(-0.05, 0.25)


def on_receive_bid(data: dict) -> dict:
    return data


def on_store_bid(entry: dict) -> dict:
    return entry


def on_sort_bids(bids: list) -> list:
    """Ordena por timestamp físico — não-determinístico em caso de empate."""
    sorted_bids = sorted(bids, key=lambda b: b["timestamp"])

    # detecta empate e exibe aviso revelador
    tie_bids = [b for b in sorted_bids if b["value"] == TIE_VALUE]
    if len(tie_bids) >= 2:
        print(f"\n  [AVISO] Empate detectado em R$ {TIE_VALUE:.2f}")
        for b in tie_bids:
            print(f"    {b['node_id']}  ts={b['timestamp']:.6f}")
        print("  [AVISO] Vencedor pode variar a cada execução.\n")

    return sorted_bids
