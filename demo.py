#!/usr/bin/env python3
"""
Demostración del crucigrama cooperativo con múltiples usuarios
"""

import time
from crucigrama_crdt import CrucigramaCRDT
from sincronizacion import ClienteP2P


def demo_basico():
    """Demostración básica con dos usuarios"""
    print("=== Demo: Crucigrama Cooperativo con CRDTs ===\n")
    
    # Crear dos crucigramas (simulando dos usuarios)
    crucigrama1 = CrucigramaCRDT(10, 10, "usuario1")
    crucigrama2 = CrucigramaCRDT(10, 10, "usuario2")
    
    print(f"Crucigrama 1 - Node ID: {crucigrama1.node_id}")
    print(f"Crucigrama 2 - Node ID: {crucigrama2.node_id}\n")
    
    # Configurar clientes P2P
    cliente1 = ClienteP2P(crucigrama1)
    cliente2 = ClienteP2P(crucigrama2)
    
    # Conectar los clientes
    cliente1.conectar_peer("usuario2", cliente2)
    cliente2.conectar_peer("usuario1", cliente1)
    
    print("Clientes conectados\n")
    
    # Usuario 1 agrega una palabra horizontal
    print("Usuario 1 agrega palabra 'PYTHON' horizontalmente en (2,1)")
    numero1 = crucigrama1.agregar_palabra(
        "Lenguaje de programación interpretado",
        "PYTHON",
        2, 1, "horizontal", "usuario1"
    )
    cliente1.enviar_cambio_local()
    time.sleep(0.1)
    
    # Usuario 2 agrega una palabra vertical que se cruza
    print("Usuario 2 agrega palabra 'HOLA' verticalmente en (1,3)")
    numero2 = crucigrama2.agregar_palabra(
        "Saludo común",
        "HOLA", 
        1, 3, "vertical", "usuario2"
    )
    cliente2.enviar_cambio_local()
    time.sleep(0.1)
    
    # Mostrar estado final de ambos crucigramas
    print("\n=== Estado final del Crucigrama 1 ===")
    mostrar_crucigrama_demo(crucigrama1)
    
    print("\n=== Estado final del Crucigrama 2 ===")
    mostrar_crucigrama_demo(crucigrama2)
    
    # Verificar que ambos tienen las mismas palabras
    print(f"\nPalabras en Crucigrama 1: {len(crucigrama1.palabras)}")
    print(f"Palabras en Crucigrama 2: {len(crucigrama2.palabras)}")
    
    print("\n=== Palabras sincronizadas ===")
    for numero, palabra in crucigrama1.palabras.items():
        print(f"{numero}. {palabra.respuesta} - {palabra.pista} (por {palabra.autor})")


def mostrar_crucigrama_demo(crucigrama):
    """Muestra el crucigrama en formato simple para la demo"""
    print("   ", end="")
    for col in range(min(8, crucigrama.columnas)):
        print(f"{col}", end=" ")
    print()
    
    for fila in range(min(8, crucigrama.filas)):
        print(f"{fila}: ", end="")
        
        for columna in range(min(8, crucigrama.columnas)):
            celda = crucigrama.obtener_celda(fila, columna)
            
            if celda and celda.es_negra:
                print("█", end=" ")
            elif celda and celda.letra:
                print(celda.letra, end=" ")
            elif celda and celda.numero:
                print(str(celda.numero), end=" ")
            else:
                print("·", end=" ")
        print()


def demo_conflictos():
    """Demostración de resolución de conflictos"""
    print("\n=== Demo: Resolución de Conflictos ===\n")
    
    crucigrama1 = CrucigramaCRDT(5, 5, "user1")
    crucigrama2 = CrucigramaCRDT(5, 5, "user2")
    
    # Simular escritura concurrente en la misma posición
    print("Ambos usuarios escriben en la posición (2,2) simultáneamente")
    
    # Usuario 1 escribe 'A'
    crucigrama1.establecer_letra(2, 2, 'A', 'user1')
    print("User1 escribe 'A'")
    
    # Usuario 2 escribe 'B' (sin sincronizar primero)
    crucigrama2.establecer_letra(2, 2, 'B', 'user2')
    print("User2 escribe 'B'")
    
    # Ahora sincronizar
    cliente1 = ClienteP2P(crucigrama1)
    cliente2 = ClienteP2P(crucigrama2)
    cliente1.conectar_peer("user2", cliente2)
    cliente2.conectar_peer("user1", cliente1)
    
    print("\nSincronizando...")
    time.sleep(0.1)
    
    # Mostrar resultado (Last Writer Wins based on timestamp)
    celda1 = crucigrama1.obtener_celda(2, 2)
    celda2 = crucigrama2.obtener_celda(2, 2)
    
    print(f"Resultado en Crucigrama 1: {celda1.letra} (autor: {celda1.autor})")
    print(f"Resultado en Crucigrama 2: {celda2.letra} (autor: {celda2.autor})")
    print("Ambos crucigramas convergen al mismo estado (Last Writer Wins)")


if __name__ == "__main__":
    demo_basico()
    demo_conflictos()