#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para sincronización por estado
"""

import time
from chat_crdt import ChatCRDT


def test_sync():
    print("=== TEST SYNC POR ESTADO ===")
    
    # Crear chats
    alice = ChatCRDT("alice")
    bob = ChatCRDT("bob")
    
    # Alice envía mensajes
    alice.enviar_mensaje("Hola Bob!")
    alice.enviar_mensaje("Como estas?")
    
    # Bob envía mensaje
    bob.enviar_mensaje("Hola Alice! Todo bien")
    
    print(f"Antes: Alice={len(alice.mensajes)}, Bob={len(bob.mensajes)}")
    
    # Sincronizar
    estado_alice = alice.obtener_estado_completo()
    bob.sincronizar_por_estado(estado_alice)
    
    estado_bob = bob.obtener_estado_completo()
    alice.sincronizar_por_estado(estado_bob)
    
    print(f"Despues: Alice={len(alice.mensajes)}, Bob={len(bob.mensajes)}")
    
    # Verificar
    if len(alice.mensajes) == len(bob.mensajes) == 3:
        print("SUCCESS: Sincronizacion por estado funciona!")
        
        alice_msgs = alice.obtener_mensajes_canal("general")
        print(f"Alice ve {len(alice_msgs)} mensajes:")
        for msg in alice_msgs:
            print(f"  {msg.autor}: {msg.contenido}")
            
        bob_msgs = bob.obtener_mensajes_canal("general")  
        print(f"Bob ve {len(bob_msgs)} mensajes:")
        for msg in bob_msgs:
            print(f"  {msg.autor}: {msg.contenido}")
        
    else:
        print("ERROR: Sincronizacion fallo")


if __name__ == "__main__":
    test_sync()