"""
DistroLeilao Inc. — Servidor Leiloeiro
=======================================
Responsável por:
  - Receber lances dos compradores
  - Manter o log de lances
  - Declarar o vencedor ao final do leilão
"""

import socket
import threading
import json
import time
import os
import importlib

# ── Configuração ──────────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 9000
AUCTION_DURATION = 15        # segundos até o leilão fechar
ITEM = "Quadro Raro — Lote #42"

# ── Injeção de bug (não mexa aqui) ────────────────────────────────────────────
BUG_MODULE = os.environ.get("DISTROLEILAO_BUG", None)
bug = importlib.import_module(BUG_MODULE) if BUG_MODULE else None

# ── Estado global ─────────────────────────────────────────────────────────────
bids = []          # lista de dicts: {node_id, value, timestamp, raw_ts}
lock = threading.Lock()
auction_open = True


def process_bid(data: dict) -> dict:
    """Processa um lance recebido. Retorna resposta ao comprador."""
    if bug:
        data = bug.on_receive_bid(data)

    with lock:
        if not auction_open:
            return {"status": "rejected", "reason": "auction_closed"}

        entry = {
            "node_id":   data["node_id"],
            "value":     data["value"],
            "timestamp": data["timestamp"],   # relógio do comprador
            "raw_ts":    time.time(),          # relógio físico do servidor
        }

        if bug:
            entry = bug.on_store_bid(entry)

        bids.append(entry)
        print(f"  [LANCE] {entry['node_id']} => R$ {entry['value']:.2f}  "
              f"(ts={entry['timestamp']}  raw={entry['raw_ts']:.4f})")

        return {"status": "accepted"}


def declare_winner():
    """Ordena lances e declara vencedor."""
    if bug:
        sorted_bids = bug.on_sort_bids(list(bids))
    else:
        sorted_bids = sorted(bids, key=lambda b: b["timestamp"])

    if not sorted_bids:
        print("\n[RESULTADO] Nenhum lance recebido.")
        return

    winner = max(sorted_bids, key=lambda b: b["value"])
    print("\n" + "="*50)
    print(f"  LEILÃO ENCERRADO — {ITEM}")
    print(f"  Vencedor : {winner['node_id']}")
    print(f"  Lance    : R$ {winner['value']:.2f}")
    print(f"  Timestamp: {winner['timestamp']}")
    print("="*50)
    print("\n  Log completo de lances (ordem de chegada ao servidor):")
    for i, b in enumerate(sorted_bids, 1):
        marker = " ◀ VENCEDOR" if b is winner else ""
        print(f"  {i}. {b['node_id']}  R$ {b['value']:.2f}  "
              f"ts={b['timestamp']}  raw={b['raw_ts']:.4f}{marker}")


def handle_client(conn, addr):
    with conn:
        raw = conn.recv(4096).decode()
        try:
            data = json.loads(raw)
            response = process_bid(data)
        except Exception as e:
            response = {"status": "error", "reason": str(e)}
        conn.sendall(json.dumps(response).encode())


def run():
    global auction_open
    print(f"[LEILOEIRO] Iniciando leilão de '{ITEM}'")
    print(f"[LEILOEIRO] Duração: {AUCTION_DURATION}s  |  Porta: {PORT}")
    if BUG_MODULE:
        print(f"[LEILOEIRO] Módulo de comportamento: {BUG_MODULE}")
    print("-"*50)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    server.settimeout(1.0)

    deadline = time.time() + AUCTION_DURATION
    while time.time() < deadline:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr),
                             daemon=True).start()
        except socket.timeout:
            continue

    auction_open = False
    server.close()
    time.sleep(0.3)   # drena últimas conexões
    declare_winner()


if __name__ == "__main__":
    run()
