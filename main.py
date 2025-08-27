#!/usr/bin/env python3
"""
Crucigrama Cooperativo con CRDTs
Sistema de crucigrama colaborativo usando Conflict-free Replicated Data Types
"""

from crucigrama_crdt import CrucigramaCRDT
from cliente import Cliente

def main():
    print("=== Crucigrama Cooperativo con CRDTs ===")
    
    # Crear instancia del crucigrama
    crucigrama = CrucigramaCRDT(15, 15)  # Grid 15x15
    
    # Crear cliente
    cliente = Cliente("usuario1", crucigrama)
    
    # Interfaz básica
    cliente.mostrar_menu()

if __name__ == "__main__":
    main()