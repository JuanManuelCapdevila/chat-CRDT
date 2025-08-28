#!/usr/bin/env python3
"""
Test de concurrencia con conexiones P2P reales
Simula 2 nodos nuevos que se conectan a la red existente y envían mensajes simultáneamente
"""

import threading
import time
import signal
import sys
from datetime import datetime
from chat_crdt import ChatCRDT
from sincronizacion_chat import ClienteP2PChat

class NodoTestConectado:
    """Simula un nodo que se conecta realmente a la red P2P"""
    
    def __init__(self, nombre_usuario: str):
        self.nombre_usuario = nombre_usuario
        self.chat = ChatCRDT(nombre_usuario)
        
        # Crear cliente P2P con autodescubrimiento habilitado
        self.cliente_p2p = ClienteP2PChat(
            self.chat, 
            nombre_usuario=nombre_usuario, 
            habilitar_autodescubrimiento=True
        )
        
        self.log = []
        self.mensajes_enviados = []
        self.activo = False
        self.nodos_conectados = set()
        
        # Configurar callbacks para monitorear conexiones
        self.cliente_p2p.establecer_callbacks_nodos(
            self._nodo_conectado,
            self._nodo_desconectado
        )
        
        # Configurar callback para cambios en CRDT
        self.chat.establecer_callback_cambio(self._chat_actualizado)
        
    def conectar(self):
        """Conecta este nodo a la red"""
        self.log_evento("Iniciando conexion a la red...")
        self.activo = True
        
        # Iniciar cliente P2P - esto activará autodescubrimiento
        self.cliente_p2p.iniciar()
        
        # Enviar mensaje de bienvenida
        self.chat.enviar_mensaje(f"{self.nombre_usuario} se ha conectado a la red!")
        
        self.log_evento(f"Conectado - Puerto: {self.cliente_p2p.puerto}")
        
    def desconectar(self):
        """Desconecta este nodo de la red"""
        if not self.activo:
            return
            
        self.log_evento("Enviando mensaje de despedida...")
        self.chat.enviar_mensaje(f"{self.nombre_usuario} se desconecta de la red")
        
        # Dar tiempo para que se sincronice el mensaje
        time.sleep(2)
        
        self.activo = False
        self.cliente_p2p.detener()
        
        self.log_evento("Desconectado")
        
    def enviar_mensaje(self, contenido: str):
        """Envía un mensaje a la red"""
        if not self.activo:
            self.log_evento("No puede enviar - no conectado")
            return None
            
        timestamp_envio = datetime.now()
        mensaje_id = self.chat.enviar_mensaje(contenido)
        
        self.mensajes_enviados.append({
            'mensaje_id': mensaje_id,
            'contenido': contenido,
            'timestamp': timestamp_envio
        })
        
        self.log_evento(f"Enviado: '{contenido}'")
        return mensaje_id
        
    def obtener_mensajes_recibidos(self):
        """Obtiene todos los mensajes en el chat local"""
        mensajes = self.chat.obtener_mensajes_canal()
        return [(m.autor, m.contenido, m.timestamp.strftime('%H:%M:%S.%f')[:-3]) for m in mensajes]
        
    def log_evento(self, mensaje):
        """Registra un evento con timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        evento = f"[{timestamp}] {self.nombre_usuario}: {mensaje}"
        self.log.append(evento)
        print(evento)  # También imprimir en consola para seguimiento en tiempo real
        
    def obtener_estadisticas(self):
        """Obtiene estadísticas del nodo"""
        stats_chat = self.chat.obtener_estadisticas()
        stats_conexion = self.cliente_p2p.obtener_estadisticas_conexion()
        
        return {
            'nombre_usuario': self.nombre_usuario,
            'puerto': self.cliente_p2p.puerto,
            'mensajes_totales': stats_chat['total_mensajes'],
            'mensajes_enviados': len(self.mensajes_enviados),
            'nodos_conocidos': stats_conexion['nodos_conocidos'],
            'conexiones_activas': stats_conexion['conexiones_activas'],
            'nodos_conectados': len(self.nodos_conectados)
        }
        
    def _nodo_conectado(self, nodo):
        """Callback cuando se conecta un nodo"""
        self.nodos_conectados.add(nodo.node_id)
        self.log_evento(f"Conectado con {nodo.nombre_usuario} ({nodo.ip_address}:{nodo.puerto})")
        
    def _nodo_desconectado(self, nodo):
        """Callback cuando se desconecta un nodo"""
        self.nodos_conectados.discard(nodo.node_id)
        self.log_evento(f"Desconectado de {nodo.nombre_usuario}")
        
    def _chat_actualizado(self):
        """Callback cuando se actualiza el chat (se recibe mensaje)"""
        self.log_evento(f"Chat actualizado - Total mensajes: {len(self.chat.mensajes)}")

def test_concurrencia_red_real():
    """Test principal de concurrencia con red real"""
    
    print("=" * 80)
    print("TEST DE CONCURRENCIA CON RED P2P REAL")
    print("=" * 80)
    print()
    
    # Variables de control para manejo de señales
    nodos_activos = []
    
    def signal_handler(signum, frame):
        print(f"\nRecibida senal {signum}, cerrando nodos...")
        for nodo in nodos_activos:
            try:
                nodo.desconectar()
            except:
                pass
        sys.exit(0)
    
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Crear dos nodos de prueba
        print("1. Creando nodos de prueba...")
        nodo_alice = NodoTestConectado("TestAlice")
        nodo_bob = NodoTestConectado("TestBob")
        nodos_activos = [nodo_alice, nodo_bob]
        
        print(f"   - Alice se conectara en puerto {nodo_alice.cliente_p2p.puerto}")
        print(f"   - Bob se conectara en puerto {nodo_bob.cliente_p2p.puerto}")
        print()
        
        # Conectar los nodos a la red
        print("2. Conectando nodos a la red...")
        nodo_alice.conectar()
        time.sleep(2)  # Esperar un poco antes de conectar el segundo
        nodo_bob.conectar()
        
        # Esperar a que se descubran mutuamente y se conecten a nodos existentes
        print("\n3. Esperando descubrimiento y conexion de nodos...")
        tiempo_espera_descubrimiento = 15
        for i in range(tiempo_espera_descubrimiento):
            print(f"   Esperando... {tiempo_espera_descubrimiento - i}s restantes", end='\r')
            time.sleep(1)
        print("\n")
        
        # Mostrar estado después del descubrimiento
        print("4. Estado despues del descubrimiento:")
        stats_alice = nodo_alice.obtener_estadisticas()
        stats_bob = nodo_bob.obtener_estadisticas()
        
        print(f"   Alice: {stats_alice['nodos_conocidos']} nodos conocidos, {stats_alice['conexiones_activas']} activas")
        print(f"   Bob: {stats_bob['nodos_conocidos']} nodos conocidos, {stats_bob['conexiones_activas']} activas")
        print()
        
        # Test de envío simultáneo de mensajes
        print("5. Enviando mensajes simultaneamente...")
        
        def enviar_rafaga_mensajes(nodo, prefijo, cantidad):
            for i in range(cantidad):
                mensaje = f"{prefijo} mensaje concurrente #{i+1}"
                nodo.enviar_mensaje(mensaje)
                time.sleep(0.5)  # Pausa pequeña entre mensajes
        
        # Crear threads para envío simultáneo
        thread_alice = threading.Thread(
            target=enviar_rafaga_mensajes, 
            args=(nodo_alice, "Alice", 3)
        )
        thread_bob = threading.Thread(
            target=enviar_rafaga_mensajes, 
            args=(nodo_bob, "Bob", 3)
        )
        
        # Iniciar envío simultáneo
        inicio_envio = time.time()
        thread_alice.start()
        thread_bob.start()
        
        # Esperar que terminen
        thread_alice.join()
        thread_bob.join()
        fin_envio = time.time()
        
        print(f"   Mensajes enviados en {fin_envio - inicio_envio:.2f}s")
        print()
        
        # Esperar sincronización
        print("6. Esperando sincronizacion de mensajes...")
        time.sleep(8)  # Dar tiempo para que se sincronicen todos los mensajes
        print()
        
        # Analizar resultados
        print("7. Analizando resultados:")
        
        # Obtener mensajes finales
        mensajes_alice = nodo_alice.obtener_mensajes_recibidos()
        mensajes_bob = nodo_bob.obtener_mensajes_recibidos()
        
        print(f"\nRESULTADOS FINALES:")
        print(f"   Alice tiene {len(mensajes_alice)} mensajes")
        print(f"   Bob tiene {len(mensajes_bob)} mensajes")
        
        print(f"\nMensajes en Alice:")
        for i, (autor, contenido, timestamp) in enumerate(mensajes_alice):
            print(f"   {i+1}. [{timestamp}] {autor}: {contenido}")
        
        print(f"\nMensajes en Bob:")  
        for i, (autor, contenido, timestamp) in enumerate(mensajes_bob):
            print(f"   {i+1}. [{timestamp}] {autor}: {contenido}")
        
        # Verificar consistencia
        mensajes_set_alice = set((autor, contenido) for autor, contenido, _ in mensajes_alice)
        mensajes_set_bob = set((autor, contenido) for autor, contenido, _ in mensajes_bob)
        
        consistencia = mensajes_set_alice == mensajes_set_bob
        
        print(f"\nEVALUACION DE CONSISTENCIA:")
        print(f"   Estados consistentes: {consistencia}")
        
        if not consistencia:
            solo_alice = mensajes_set_alice - mensajes_set_bob
            solo_bob = mensajes_set_bob - mensajes_set_alice
            
            if solo_alice:
                print(f"   Solo en Alice: {solo_alice}")
            if solo_bob:
                print(f"   Solo en Bob: {solo_bob}")
        else:
            print("   Los nodos tienen los mismos mensajes despues de sincronizacion")
        
        # Estadísticas finales
        stats_alice = nodo_alice.obtener_estadisticas()
        stats_bob = nodo_bob.obtener_estadisticas()
        
        print(f"\nESTADISTICAS FINALES:")
        print(f"   Alice: {stats_alice['mensajes_enviados']} enviados, {stats_alice['mensajes_totales']} totales")
        print(f"   Bob: {stats_bob['mensajes_enviados']} enviados, {stats_bob['mensajes_totales']} totales")
        
        # Mantener conexión abierta para observación
        print(f"\nMANTENIENDO CONEXION PARA OBSERVACION...")
        print(f"Los nodos permaneceran conectados por 30 segundos adicionales.")
        print(f"Puedes observar la actividad en tu nodo principal.")
        print(f"Presiona Ctrl+C para terminar antes.")
        
        for i in range(30):
            try:
                print(f"   Tiempo restante: {30-i}s (Alice: {len(nodo_alice.nodos_conectados)} conexiones, Bob: {len(nodo_bob.nodos_conectados)} conexiones)", end='\r')
                time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n   Terminando por solicitud del usuario...")
                break
        
        print(f"\n")
        
    except KeyboardInterrupt:
        print(f"\nTest interrumpido por el usuario")
    
    except Exception as e:
        print(f"\nERROR DURANTE EL TEST: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Limpiar conexiones
        print(f"\nDesconectando nodos...")
        for nodo in nodos_activos:
            try:
                nodo.desconectar()
            except Exception as e:
                print(f"Error desconectando nodo: {e}")
        
        print(f"\nTest de red real completado")

if __name__ == "__main__":
    test_concurrencia_red_real()