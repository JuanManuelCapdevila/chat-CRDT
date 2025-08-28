#!/usr/bin/env python3
"""
Test de concurrencia para el chat CRDT
Simula 2 nodos enviando mensajes simultáneamente
"""

import threading
import time
import uuid
from datetime import datetime
from chat_crdt import ChatCRDT

class SimuladorNodo:
    """Simula un nodo de chat para pruebas de concurrencia"""
    
    def __init__(self, nombre_usuario: str):
        self.nombre_usuario = nombre_usuario
        self.chat = ChatCRDT(nombre_usuario)
        self.mensajes_enviados = []
        self.log = []
        
    def enviar_mensaje(self, contenido: str):
        """Envía un mensaje y registra la acción"""
        timestamp_envio = datetime.now()
        mensaje_id = self.chat.enviar_mensaje(contenido)
        
        self.mensajes_enviados.append({
            'mensaje_id': mensaje_id,
            'contenido': contenido,
            'timestamp_envio': timestamp_envio
        })
        
        self.log.append(f"[{timestamp_envio.strftime('%H:%M:%S.%f')[:-3]}] {self.nombre_usuario}: Enviado '{contenido}'")
        
        return mensaje_id
    
    def sincronizar_con_nodo(self, otro_nodo):
        """Sincroniza con otro nodo"""
        timestamp_sync = datetime.now()
        estado_antes = len(self.chat.mensajes)
        
        # Obtener estado del otro nodo y sincronizar
        estado_remoto = otro_nodo.chat.obtener_estado_completo()
        cambios = self.chat.sincronizar_por_estado(estado_remoto)
        
        estado_despues = len(self.chat.mensajes)
        
        if cambios:
            self.log.append(f"[{timestamp_sync.strftime('%H:%M:%S.%f')[:-3]}] {self.nombre_usuario}: Sincronizado con {otro_nodo.nombre_usuario} - Mensajes: {estado_antes} -> {estado_despues}")
        
        return cambios
    
    def obtener_mensajes_ordenados(self):
        """Obtiene mensajes ordenados por timestamp"""
        mensajes = self.chat.obtener_mensajes_canal()
        return [(m.autor, m.contenido, m.timestamp.strftime('%H:%M:%S.%f')[:-3]) for m in mensajes]

def test_concurrencia_basico():
    """Test básico de concurrencia - 2 nodos enviando mensajes simultáneamente"""
    
    print("=== TEST DE CONCURRENCIA BÁSICO ===\n")
    
    # Crear dos nodos
    nodo1 = SimuladorNodo("Alice")
    nodo2 = SimuladorNodo("Bob")
    
    # Función para que un nodo envíe múltiples mensajes
    def enviar_mensajes_nodo(nodo, prefijo, cantidad, delay):
        for i in range(cantidad):
            mensaje = f"{prefijo} mensaje {i+1}"
            nodo.enviar_mensaje(mensaje)
            time.sleep(delay)
    
    print("1. Enviando mensajes simultáneamente desde ambos nodos...\n")
    
    # Crear threads para envío simultáneo
    thread1 = threading.Thread(target=enviar_mensajes_nodo, args=(nodo1, "Alice:", 3, 0.1))
    thread2 = threading.Thread(target=enviar_mensajes_nodo, args=(nodo2, "Bob:", 3, 0.15))
    
    # Iniciar ambos threads al mismo tiempo
    start_time = time.time()
    thread1.start()
    thread2.start()
    
    # Esperar que terminen
    thread1.join()
    thread2.join()
    
    end_time = time.time()
    
    print(f"Tiempo total de envío: {end_time - start_time:.3f} segundos\n")
    
    # Mostrar estado de cada nodo antes de sincronizar
    print("2. Estado de cada nodo ANTES de sincronizar:")
    print(f"\nNodo Alice ({len(nodo1.chat.mensajes)} mensajes):")
    for autor, contenido, timestamp in nodo1.obtener_mensajes_ordenados():
        print(f"  [{timestamp}] {autor}: {contenido}")
    
    print(f"\nNodo Bob ({len(nodo2.chat.mensajes)} mensajes):")
    for autor, contenido, timestamp in nodo2.obtener_mensajes_ordenados():
        print(f"  [{timestamp}] {autor}: {contenido}")
    
    # Sincronizar los nodos
    print(f"\n3. Sincronizando nodos...")
    sync_time = time.time()
    
    # Sincronización bidireccional
    cambios1 = nodo1.sincronizar_con_nodo(nodo2)
    cambios2 = nodo2.sincronizar_con_nodo(nodo1)
    
    print(f"   - Alice recibió cambios: {cambios1}")
    print(f"   - Bob recibió cambios: {cambios2}")
    
    # Mostrar estado después de sincronizar
    print(f"\n4. Estado de cada nodo DESPUÉS de sincronizar:")
    print(f"\nNodo Alice ({len(nodo1.chat.mensajes)} mensajes):")
    for autor, contenido, timestamp in nodo1.obtener_mensajes_ordenados():
        print(f"  [{timestamp}] {autor}: {contenido}")
    
    print(f"\nNodo Bob ({len(nodo2.chat.mensajes)} mensajes):")
    for autor, contenido, timestamp in nodo2.obtener_mensajes_ordenados():
        print(f"  [{timestamp}] {autor}: {contenido}")
    
    # Verificar consistencia
    mensajes_alice = set((m.mensaje_id, m.contenido, m.autor) for m in nodo1.chat.mensajes.values())
    mensajes_bob = set((m.mensaje_id, m.contenido, m.autor) for m in nodo2.chat.mensajes.values())
    
    print(f"\n5. Verificación de consistencia:")
    print(f"   - Mensajes en Alice: {len(mensajes_alice)}")
    print(f"   - Mensajes en Bob: {len(mensajes_bob)}")
    print(f"   - Estados consistentes: {mensajes_alice == mensajes_bob}")
    
    if mensajes_alice != mensajes_bob:
        print("   INCONSISTENCIA DETECTADA!")
        solo_alice = mensajes_alice - mensajes_bob
        solo_bob = mensajes_bob - mensajes_alice
        if solo_alice:
            print(f"   - Solo en Alice: {solo_alice}")
        if solo_bob:
            print(f"   - Solo en Bob: {solo_bob}")
    else:
        print("   Estados consistentes despues de sincronizacion")
    
    # Mostrar logs de actividad
    print(f"\n6. Logs de actividad:")
    print(f"\nAlice:")
    for log_entry in nodo1.log:
        print(f"  {log_entry}")
    
    print(f"\nBob:")
    for log_entry in nodo2.log:
        print(f"  {log_entry}")

def test_concurrencia_intensivo():
    """Test intensivo - simula condiciones de carrera más extremas"""
    
    print("\n\n=== TEST DE CONCURRENCIA INTENSIVO ===\n")
    
    nodo1 = SimuladorNodo("Node_1")
    nodo2 = SimuladorNodo("Node_2")
    
    # Variables compartidas para sincronización
    barrier = threading.Barrier(2)  # Para sincronizar inicio
    resultados = {}
    
    def enviar_rafaga_mensajes(nodo, node_id, mensaje_base, cantidad):
        """Envía una ráfaga de mensajes en el tiempo más corto posible"""
        
        # Esperar que ambos threads estén listos
        barrier.wait()
        
        start_time = time.time()
        mensajes_enviados = []
        
        # Enviar mensajes lo más rápido posible
        for i in range(cantidad):
            timestamp_antes = time.time()
            mensaje_id = nodo.enviar_mensaje(f"{mensaje_base}_{i}")
            timestamp_despues = time.time()
            
            mensajes_enviados.append({
                'id': mensaje_id,
                'time_start': timestamp_antes,
                'time_end': timestamp_despues,
                'duration': timestamp_despues - timestamp_antes
            })
        
        end_time = time.time()
        
        resultados[node_id] = {
            'total_time': end_time - start_time,
            'mensajes': mensajes_enviados,
            'avg_time_per_msg': (end_time - start_time) / cantidad
        }
    
    print("1. Enviando ráfagas de mensajes simultáneas...\n")
    
    # Crear threads para ráfagas simultáneas
    thread1 = threading.Thread(target=enviar_rafaga_mensajes, args=(nodo1, 'node1', 'RAPID_MSG_A', 5))
    thread2 = threading.Thread(target=enviar_rafaga_mensajes, args=(nodo2, 'node2', 'RAPID_MSG_B', 5))
    
    # Iniciar threads
    thread1.start()
    thread2.start()
    
    # Esperar que terminen
    thread1.join()
    thread2.join()
    
    # Mostrar resultados de rendimiento
    print("2. Resultados de rendimiento:")
    for node_id, stats in resultados.items():
        print(f"\n{node_id.upper()}:")
        print(f"  - Tiempo total: {stats['total_time']:.4f}s")
        print(f"  - Tiempo promedio por mensaje: {stats['avg_time_per_msg']:.4f}s")
        if stats['total_time'] > 0:
            print(f"  - Mensajes por segundo: {len(stats['mensajes'])/stats['total_time']:.2f}")
        else:
            print(f"  - Mensajes por segundo: INSTANTANEO (tiempo muy pequeno)")
    
    # Verificar estado antes de sync
    print(f"\n3. Estado antes de sincronización:")
    print(f"   - Node_1 tiene {len(nodo1.chat.mensajes)} mensajes")
    print(f"   - Node_2 tiene {len(nodo2.chat.mensajes)} mensajes")
    
    # Sincronizar y verificar
    print(f"\n4. Sincronizando...")
    nodo1.sincronizar_con_nodo(nodo2)
    nodo2.sincronizar_con_nodo(nodo1)
    
    print(f"   - Node_1 después: {len(nodo1.chat.mensajes)} mensajes")
    print(f"   - Node_2 después: {len(nodo2.chat.mensajes)} mensajes")
    
    # Análisis final
    todos_mensajes_n1 = nodo1.obtener_mensajes_ordenados()
    todos_mensajes_n2 = nodo2.obtener_mensajes_ordenados()
    
    print(f"\n5. Análisis de orden temporal:")
    print("Orden de mensajes después de sincronización:")
    
    for i, (autor, contenido, timestamp) in enumerate(todos_mensajes_n1[:10]):  # Mostrar solo primeros 10
        print(f"  {i+1}. [{timestamp}] {autor}: {contenido}")
    
    # Verificar que el orden es el mismo en ambos nodos
    orden_consistente = todos_mensajes_n1 == todos_mensajes_n2
    print(f"\n6. Orden consistente entre nodos: {orden_consistente}")
    
    if not orden_consistente:
        print("   ORDEN INCONSISTENTE DETECTADO!")

def main():
    """Función principal que ejecuta todos los tests"""
    
    print("INICIANDO TESTS DE CONCURRENCIA PARA CHAT CRDT")
    print("=" * 60)
    
    try:
        # Test básico
        test_concurrencia_basico()
        
        # Test intensivo 
        test_concurrencia_intensivo()
        
        print("\n" + "=" * 60)
        print("TESTS DE CONCURRENCIA COMPLETADOS")
        
    except Exception as e:
        print(f"\nERROR DURANTE LOS TESTS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()