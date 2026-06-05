"""
DistroLeilao Inc. — Nó Comprador
==================================
Cada instância representa um comprador em um nó diferente.
Uso:
    python buyer.py <NODE_ID> <LANCE_1> [LANCE_2 ...]

Exemplo:
    python buyer.py Node-A 100 150 200
"""

import socket
import json
import time
import sys
import random
import os
import importlib

# ── Configuração ──────────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 9000

# ── Injeção de bug ────────────────────────────────────────────────────────────
BUG_MODULE = os.environ.get("DISTROLEILAO_BUG", None)
bug = importlib.import_module(BUG_MODULE) if BUG_MODULE else None

# ── Estado do comprador ───────────────────────────────────────────────────────
local_clock = 0     # relógio lógico local (simples contador)


def get_timestamp() -> int:
    """Retorna o timestamp lógico atual e incrementa o relógio."""
    global local_clock
    local_clock += 1
    if bug:
        return bug.on_get_timestamp(local_clock)
    return local_clock


def send_bid(node_id: str, value: float) -> dict:
    """Envia um lance ao leiloeiro e retorna a resposta."""
    ts = get_timestamp()

    payload = {
        "node_id":   node_id,
        "value":     value,
        "timestamp": ts,
    }

    if bug:
        payload = bug.on_send_bid(payload)

    # simula latência de rede variável (entre nós distintos)
    network_delay = random.uniform(0.05, 0.3)
    if bug:
        network_delay = bug.on_network_delay(network_delay)
    time.sleep(network_delay)

    try:
        with socket.create_connection((HOST, PORT), timeout=5) as s:
            s.sendall(json.dumps(payload).encode())
            response = json.loads(s.recv(1024).decode())
    except Exception as e:
        response = {"status": "error", "reason": str(e)}

    print(f"  [{node_id}] Lance R$ {value:.2f}  ts={ts}  "
          f"delay={network_delay:.3f}s  => {response['status']}")
    return response


def run(node_id: str, values: list[float]):
    global local_clock

    if bug:
        local_clock = bug.on_startup(node_id, local_clock)

    print(f"[{node_id}] Comprador iniciado  |  lances planejados: {values}")
    for v in values:
        send_bid(node_id, v)
        time.sleep(random.uniform(0.1, 0.5))

    print(f"[{node_id}] Todos os lances enviados.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python buyer.py <NODE_ID> <LANCE_1> [LANCE_2 ...]")
        sys.exit(1)

    node_id = sys.argv[1]
    bids    = [float(x) for x in sys.argv[2:]]
    run(node_id, bids)
