#!/usr/bin/env python3
"""
Test simple del autodescubrimiento de nodos
"""

import time
import threading
from chat_crdt import ChatCRDT
from sincronizacion_chat import ClienteP2PChat


def crear_usuario_test(nombre: str, puerto: int = 0):
    """Crea un usuario de test"""
    print(f">> Creando usuario: {nombre}")
    
    chat = ChatCRDT(nombre)
    chat.enviar_mensaje(f"¡Hola! Soy {nombre}")
    
    cliente = ClienteP2PChat(chat, nombre, puerto=puerto)
    
    def nodo_conectado(nodo):
        print(f"[OK] {nombre} descubrio nodo: {nodo.nombre_usuario} ({nodo.ip_address}:{nodo.puerto})")
    
    def nodo_desconectado(nodo):
        print(f"[X] {nombre} perdio nodo: {nodo.nombre_usuario}")
    
    cliente.establecer_callbacks_nodos(nodo_conectado, nodo_desconectado)
    cliente.iniciar()
    
    print(f"   Puerto asignado: {cliente.puerto}")
    return cliente


def main():
    print("=== PRUEBA DE AUTODESCUBRIMIENTO DE NODOS ===\n")
    
    # Crear dos usuarios con puertos en el mismo rango
    print("1. Creando usuarios...")
    usuario1 = crear_usuario_test("Alice", puerto=12001)
    time.sleep(2)
    
    usuario2 = crear_usuario_test("Bob", puerto=12002)
    time.sleep(2)
    
    usuario3 = crear_usuario_test("Charlie", puerto=12003)
    
    print(f"\n2. Usuarios creados:")
    print(f"   Alice: puerto {usuario1.puerto}")
    print(f"   Bob: puerto {usuario2.puerto}")
    print(f"   Charlie: puerto {usuario3.puerto}")
    
    print("\n3. Esperando autodescubrimiento (30 segundos)...")
    
    # Esperar y mostrar estado periódicamente
    for i in range(6):
        time.sleep(5)
        print(f"\n--- Después de {(i+1)*5} segundos ---")
        
        for nombre, cliente in [("Alice", usuario1), ("Bob", usuario2), ("Charlie", usuario3)]:
            nodos = cliente.obtener_nodos_descubiertos()
            conexiones = len(cliente.conexiones_activas)
            print(f"{nombre}: {len(nodos)} nodos descubiertos, {conexiones} conexiones activas")
            
            for nodo in nodos:
                estado = "[ON]" if nodo.node_id in cliente.conexiones_activas else "[OFF]"
                print(f"  {estado} {nodo.nombre_usuario} ({nodo.ip_address}:{nodo.puerto})")
    
    # Mostrar estado final
    print(f"\n4. Estado final:")
    print(f"   Alice conoce: {[n.nombre_usuario for n in usuario1.obtener_nodos_descubiertos()]}")
    print(f"   Bob conoce: {[n.nombre_usuario for n in usuario2.obtener_nodos_descubiertos()]}")
    print(f"   Charlie conoce: {[n.nombre_usuario for n in usuario3.obtener_nodos_descubiertos()]}")
    
    # Probar envío de mensajes
    print(f"\n5. Probando intercambio de mensajes...")
    usuario1.chat.enviar_mensaje("¡Hola Bob y Charlie! - Alice")
    usuario2.chat.enviar_mensaje("¡Hola Alice y Charlie! - Bob")
    usuario3.chat.enviar_mensaje("¡Hola Alice y Bob! - Charlie")
    
    time.sleep(3)
    
    print(f"\n6. Mensajes en cada chat:")
    for nombre, cliente in [("Alice", usuario1), ("Bob", usuario2), ("Charlie", usuario3)]:
        mensajes = cliente.chat.obtener_mensajes_canal("general")
        print(f"\n{nombre} tiene {len(mensajes)} mensajes:")
        for msg in mensajes:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            print(f"  [{timestamp}] {msg.autor}: {msg.contenido}")
    
    # Limpiar
    print(f"\n7. Deteniendo clientes...")
    usuario1.detener()
    usuario2.detener()
    usuario3.detener()
    
    print("[OK] Prueba completada")


if __name__ == "__main__":
    main()