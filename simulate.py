"""
DistroLeilao Inc. — Simulação Automática
=========================================
Inicia o leiloeiro e os 3 compradores automaticamente.
Útil para reproduzir o comportamento e coletar logs.

Uso:
    python simulate.py
"""

import subprocess
import sys
import time
import os

PYTHON = sys.executable
ENV    = {**os.environ, "DISTROLEILAO_BUG": "network"}


def run():
    print("=" * 55)
    print("  DistroLeilao Inc. — Simulação")
    print("=" * 55 + "\n")

    auctioneer = subprocess.Popen([PYTHON, "auctioneer.py"], env=ENV)
    time.sleep(0.5)

    buyers = [
        subprocess.Popen([PYTHON, "buyer.py", "Node-A", "300", "450"], env=ENV),
        subprocess.Popen([PYTHON, "buyer.py", "Node-B", "500", "480"], env=ENV),
        subprocess.Popen([PYTHON, "buyer.py", "Node-C", "350", "510"], env=ENV),
    ]

    for b in buyers:
        b.wait()

    auctioneer.wait()
    print("\n[simulação encerrada]")


if __name__ == "__main__":
    run()
