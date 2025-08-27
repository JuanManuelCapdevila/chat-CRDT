#!/usr/bin/env python3
"""
Test simple para verificar puertos
"""

import socket
import time
from sincronizacion_chat import ClienteP2PChat
from chat_crdt import ChatCRDT


def test_puertos():
    print("=== TEST DE PUERTOS ===")
    
    # Crear cliente
    chat = ChatCRDT("TestUser")
    cliente = ClienteP2PChat(chat, "TestUser", puerto=12005)
    
    print(f"Puerto asignado al cliente: {cliente.puerto}")
    
    # Verificar que el puerto esté libre
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', cliente.puerto))
            print(f"Puerto {cliente.puerto} está libre")
    except OSError as e:
        print(f"Puerto {cliente.puerto} NO está libre: {e}")
    
    # Iniciar cliente
    cliente.iniciar()
    time.sleep(2)
    
    # Verificar que el servidor esté escuchando
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', cliente.puerto))
            if result == 0:
                print(f"Servidor está escuchando en puerto {cliente.puerto}")
            else:
                print(f"Servidor NO está escuchando en puerto {cliente.puerto}")
    except Exception as e:
        print(f"Error probando conexión: {e}")
    
    # Detener
    cliente.detener()
    print("Test completado")


if __name__ == "__main__":
    test_puertos()