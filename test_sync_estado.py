#!/usr/bin/env python3
"""
Test específico para sincronización por estado
"""

import time
from chat_crdt import ChatCRDT


def test_sincronizacion_estado():
    print("=== TEST SINCRONIZACIÓN POR ESTADO ===\n")
    
    # Crear dos chats
    print("1. Creando chats...")
    chat_alice = ChatCRDT("alice")
    chat_bob = ChatCRDT("bob")
    
    print(f"Alice vector clock inicial: {chat_alice.vector_clock}")
    print(f"Bob vector clock inicial: {chat_bob.vector_clock}")
    
    # Alice envía mensajes
    print("\n2. Alice envía mensajes...")
    msg1 = chat_alice.enviar_mensaje("Hola Bob!")
    msg2 = chat_alice.enviar_mensaje("¿Cómo estás?")
    
    print(f"Alice tiene {len(chat_alice.mensajes)} mensajes")
    print(f"Alice vector clock: {chat_alice.vector_clock}")
    
    # Bob también envía mensaje
    print("\n3. Bob envía mensaje...")
    msg3 = chat_bob.enviar_mensaje("¡Hola Alice! Todo bien")
    
    print(f"Bob tiene {len(chat_bob.mensajes)} mensajes")
    print(f"Bob vector clock: {chat_bob.vector_clock}")
    
    # Estado antes de sincronizar
    print("\n4. Estado antes de sincronizar:")
    print(f"Alice conoce: {len(chat_alice.mensajes)} mensajes")
    print(f"Bob conoce: {len(chat_bob.mensajes)} mensajes")
    
    # Sincronizar estado de Alice hacia Bob
    print("\n5. Sincronizando estado de Alice hacia Bob...")
    estado_alice = chat_alice.obtener_estado_completo()
    cambios_bob = chat_bob.sincronizar_por_estado(estado_alice)
    
    print(f"¿Bob tuvo cambios? {cambios_bob}")
    print(f"Bob vector clock después: {chat_bob.vector_clock}")
    
    # Sincronizar estado de Bob hacia Alice
    print("\n6. Sincronizando estado de Bob hacia Alice...")
    estado_bob = chat_bob.obtener_estado_completo()
    cambios_alice = chat_alice.sincronizar_por_estado(estado_bob)
    
    print(f"¿Alice tuvo cambios? {cambios_alice}")
    print(f"Alice vector clock después: {chat_alice.vector_clock}")
    
    # Estado después de sincronizar
    print("\n7. Estado después de sincronizar:")
    print(f"Alice conoce: {len(chat_alice.mensajes)} mensajes")
    print(f"Bob conoce: {len(chat_bob.mensajes)} mensajes")
    
    # Mostrar mensajes finales
    print("\n8. Mensajes en Alice:")
    mensajes_alice = chat_alice.obtener_mensajes_canal("general")
    for msg in mensajes_alice:
        timestamp_str = msg.timestamp.strftime("%H:%M:%S")
        print(f"   [{timestamp_str}] {msg.autor}: {msg.contenido}")
    
    print("\n9. Mensajes en Bob:")
    mensajes_bob = chat_bob.obtener_mensajes_canal("general")
    for msg in mensajes_bob:
        timestamp_str = msg.timestamp.strftime("%H:%M:%S")
        print(f"   [{timestamp_str}] {msg.autor}: {msg.contenido}")
    
    # Verificar convergencia
    print(f"\n10. Verificación de convergencia:")
    if len(chat_alice.mensajes) == len(chat_bob.mensajes):
        print("[OK] Ambos chats tienen el mismo numero de mensajes")
        
        # Verificar que son los mismos mensajes
        alice_ids = set(chat_alice.mensajes.keys())
        bob_ids = set(chat_bob.mensajes.keys())
        
        if alice_ids == bob_ids:
            print("[OK] Ambos chats tienen los mismos mensajes (IDs coinciden)")
            
            # Verificar contenido
            contenidos_iguales = True
            for msg_id in alice_ids:
                alice_msg = chat_alice.mensajes[msg_id]
                bob_msg = chat_bob.mensajes[msg_id]
                
                if (alice_msg.contenido != bob_msg.contenido or 
                    alice_msg.autor != bob_msg.autor):
                    contenidos_iguales = False
                    break
            
            if contenidos_iguales:
                print("[OK] El contenido de todos los mensajes coincide")
                print("SUCCESS: SINCRONIZACION POR ESTADO EXITOSA!")
            else:
                print("[ERROR] El contenido de algunos mensajes no coincide")
        else:
            print("[ERROR] Los chats tienen mensajes diferentes")
            print(f"Solo en Alice: {alice_ids - bob_ids}")
            print(f"Solo en Bob: {bob_ids - alice_ids}")
    else:
        print(f"[ERROR] Diferentes numeros de mensajes: Alice({len(chat_alice.mensajes)}) vs Bob({len(chat_bob.mensajes)})")


if __name__ == "__main__":
    test_sincronizacion_estado()