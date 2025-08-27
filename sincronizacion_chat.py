#!/usr/bin/env python3
"""
Sistema de sincronización P2P para el chat cooperativo
"""

import asyncio
import json
import uuid
import socket
import threading
import logging
import time
from typing import Dict, Set, Optional, List, Any
from dataclasses import asdict
from chat_crdt import ChatCRDT, Mensaje, Operacion
from crdt_base import Timestamp
from descubrimiento_nodos import GestorDescubrimiento, TipoDescubrimiento, InfoNodo


class SincronizadorChat:
    """Maneja la sincronización entre diferentes instancias del chat"""
    
    def __init__(self, chat: ChatCRDT):
        self.chat = chat
        self.clientes_conectados: Set[str] = set()
        self.ultimo_sync_timestamp: Optional[Timestamp] = None
        
    def registrar_cliente(self, cliente_id: str):
        """Registra un nuevo cliente"""
        self.clientes_conectados.add(cliente_id)
        
    def desregistrar_cliente(self, cliente_id: str):
        """Desregistra un cliente"""
        self.clientes_conectados.discard(cliente_id)
        
    def obtener_actualizaciones_desde(self, timestamp: Optional[Timestamp] = None) -> Dict:
        """Obtiene el estado completo para sincronización por estado"""
        return {
            'tipo_sync': 'estado',
            'estado_completo': self.chat.obtener_estado_completo(),
            'vector_clock': self.chat.vector_clock.copy()
        }
    
    def aplicar_actualizaciones(self, datos_sync: Dict):
        """Aplica actualizaciones recibidas de otros clientes"""
        tipo_sync = datos_sync.get('tipo_sync', 'operaciones')
        
        if tipo_sync == 'estado' and 'estado_completo' in datos_sync:
            # Sincronización por estado
            self.chat.sincronizar_por_estado(datos_sync['estado_completo'])
        elif 'operaciones' in datos_sync:
            # Sincronización por operaciones (fallback)
            operaciones = [self._deserializar_operacion(op) for op in datos_sync['operaciones']]
            self.chat.sincronizar_con(operaciones)
    
    def _serializar_operacion(self, operacion: Operacion) -> Dict:
        """Convierte una operación a formato JSON"""
        return {
            'tipo': operacion.tipo,
            'clave': operacion.clave,
            'valor': operacion.valor,
            'timestamp': {
                'node_id': operacion.timestamp.node_id,
                'counter': operacion.timestamp.counter
            },
            'usuario': operacion.usuario
        }
    
    def _deserializar_operacion(self, datos: Dict) -> Operacion:
        """Convierte datos JSON a operación"""
        timestamp = Timestamp(
            datos['timestamp']['node_id'],
            datos['timestamp']['counter']
        )
        
        return Operacion(
            tipo=datos['tipo'],
            clave=datos['clave'],
            valor=datos['valor'],
            timestamp=timestamp,
            usuario=datos['usuario']
        )


class ClienteP2PChat:
    """
    Cliente P2P para sincronización de chat
    Maneja descubrimiento de nodos y comunicación
    """
    
    def __init__(self, chat: ChatCRDT, nombre_usuario: str = None, 
                 puerto: int = 0, habilitar_autodescubrimiento: bool = True):
        self.chat = chat
        self.nombre_usuario = nombre_usuario or chat.usuario_id
        # Usar puerto base estándar o el especificado
        self.puerto = puerto or self._obtener_puerto_en_rango()
        self.sincronizador = SincronizadorChat(chat)
        
        # Estado de conexión
        self.activo = False
        self.nodos_conocidos: Dict[str, InfoNodo] = {}
        self.conexiones_activas: Dict[str, socket.socket] = {}
        
        # Autodescubrimiento
        self.habilitar_autodescubrimiento = habilitar_autodescubrimiento
        self.gestor_descubrimiento = None
        
        # Threading
        self.servidor_thread = None
        self.sync_thread = None
        self.logger = logging.getLogger(f"ClienteP2PChat-{self.nombre_usuario}")
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        
        # Callbacks para UI
        self.callback_nodo_conectado = None
        self.callback_nodo_desconectado = None
        
    def establecer_callbacks_nodos(self, callback_conectado, callback_desconectado):
        """Establece callbacks para notificar cambios en nodos"""
        self.callback_nodo_conectado = callback_conectado
        self.callback_nodo_desconectado = callback_desconectado
        
    def _obtener_puerto_libre(self) -> int:
        """Encuentra un puerto libre para el servidor"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            return s.getsockname()[1]
    
    def _obtener_puerto_en_rango(self, puerto_base: int = 12000) -> int:
        """Obtiene un puerto libre en un rango específico para facilitar descubrimiento"""
        for puerto in range(puerto_base, puerto_base + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', puerto))
                    return puerto
            except OSError:
                continue
        
        # Si no encuentra ninguno en el rango, usar puerto aleatorio
        return self._obtener_puerto_libre()
    
    def iniciar(self):
        """Inicia el cliente P2P"""
        if self.activo:
            return
        
        self.activo = True
        self.logger.info(f"Iniciando cliente P2P en puerto {self.puerto}")
        
        # Iniciar servidor
        self.servidor_thread = threading.Thread(target=self._ejecutar_servidor, daemon=True)
        self.servidor_thread.start()
        
        # Iniciar sincronización periódica
        self.sync_thread = threading.Thread(target=self._bucle_sincronizacion, daemon=True)
        self.sync_thread.start()
        
        # Iniciar autodescubrimiento si está habilitado
        if self.habilitar_autodescubrimiento:
            self.iniciar_autodescubrimiento()
    
    def detener(self):
        """Detiene el cliente P2P"""
        self.activo = False
        
        # Cerrar conexiones
        for conexion in self.conexiones_activas.values():
            try:
                conexion.close()
            except:
                pass
        self.conexiones_activas.clear()
        
        # Detener autodescubrimiento
        if self.gestor_descubrimiento:
            self.gestor_descubrimiento.detener_todos()
        
        self.logger.info("Cliente P2P detenido")
    
    def iniciar_autodescubrimiento(self):
        """Inicia el sistema de autodescubrimiento"""
        if self.gestor_descubrimiento:
            return
        
        try:
            self.gestor_descubrimiento = GestorDescubrimiento(
                self.chat.usuario_id,
                self.nombre_usuario
            )
            
            # Configurar puerto del chat en los descubridores
            self.puerto_chat = self.puerto
            
            # Configurar callback
            def callback_consolidado(accion, nodo):
                if accion == "descubierto":
                    self._nodo_descubierto(nodo)
                elif accion == "perdido":
                    self._nodo_perdido(nodo)
            
            self.gestor_descubrimiento.callbacks_cambio.append(callback_consolidado)
            
            # Agregar algoritmos de descubrimiento usando rango de puertos estándar
            self.gestor_descubrimiento.agregar_descubridor(TipoDescubrimiento.UDP_BROADCAST, 12000)
            self.gestor_descubrimiento.agregar_descubridor(TipoDescubrimiento.SCAN_PUERTOS, 12000)
            
            # Configurar el puerto del chat en los descubridores
            for descubridor in self.gestor_descubrimiento.descubridores.values():
                descubridor.establecer_puerto_chat(self.puerto)
            
            self.gestor_descubrimiento.iniciar_todos()
            
            self.logger.info("Autodescubrimiento iniciado")
            
        except Exception as e:
            self.logger.error(f"Error al iniciar autodescubrimiento: {e}")
    
    def _nodo_descubierto(self, nodo: InfoNodo):
        """Callback cuando se descubre un nuevo nodo"""
        if nodo.node_id != self.chat.usuario_id and nodo.node_id not in self.nodos_conocidos:
            self.nodos_conocidos[nodo.node_id] = nodo
            self.logger.info(f"Descubierto nodo: {nodo.nombre_usuario} ({nodo.ip_address}:{nodo.puerto})")
            
            # Notificar a la UI
            if self.callback_nodo_conectado:
                self.callback_nodo_conectado(nodo)
            
            # Intentar conectar al nodo
            self._conectar_a_nodo(nodo)
    
    def _nodo_perdido(self, nodo: InfoNodo):
        """Callback cuando se pierde un nodo"""
        if nodo.node_id in self.nodos_conocidos:
            del self.nodos_conocidos[nodo.node_id]
            self.logger.info(f"Nodo perdido: {nodo.nombre_usuario}")
            
            # Notificar a la UI
            if self.callback_nodo_desconectado:
                self.callback_nodo_desconectado(nodo)
            
            # Cerrar conexión si existe
            if nodo.node_id in self.conexiones_activas:
                try:
                    self.conexiones_activas[nodo.node_id].close()
                except:
                    pass
                del self.conexiones_activas[nodo.node_id]
    
    def _conectar_a_nodo(self, nodo: InfoNodo):
        """Intenta conectarse a un nodo descubierto"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((nodo.ip_address, nodo.puerto))
            
            self.conexiones_activas[nodo.node_id] = sock
            self.sincronizador.registrar_cliente(nodo.node_id)
            
            # Realizar sincronización inicial
            self._sincronizar_con_nodo(nodo.node_id)
            
            self.logger.info(f"Conectado a nodo {nodo.nombre_usuario}")
            
        except Exception as e:
            self.logger.error(f"Error conectando a nodo {nodo.nombre_usuario}: {e}")
    
    def _ejecutar_servidor(self):
        """Ejecuta el servidor que acepta conexiones entrantes"""
        try:
            servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            servidor.bind(('localhost', self.puerto))
            servidor.listen(5)
            servidor.settimeout(1)
            
            self.logger.info(f"Servidor escuchando en puerto {self.puerto}")
            
            while self.activo:
                try:
                    cliente_sock, direccion = servidor.accept()
                    
                    # Manejar conexión en hilo separado
                    thread_cliente = threading.Thread(
                        target=self._manejar_cliente,
                        args=(cliente_sock, direccion),
                        daemon=True
                    )
                    thread_cliente.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.activo:
                        self.logger.error(f"Error en servidor: {e}")
            
            servidor.close()
            
        except Exception as e:
            self.logger.error(f"Error fatal en servidor: {e}")
    
    def _manejar_cliente(self, cliente_sock: socket.socket, direccion):
        """Maneja una conexión de cliente entrante"""
        try:
            cliente_sock.settimeout(30)
            
            while self.activo:
                # Recibir mensaje
                data = cliente_sock.recv(4096)
                if not data:
                    break
                
                mensaje = json.loads(data.decode())
                respuesta = self._procesar_mensaje(mensaje)
                
                # Enviar respuesta
                respuesta_json = json.dumps(respuesta).encode()
                cliente_sock.send(respuesta_json)
                
        except Exception as e:
            self.logger.error(f"Error manejando cliente {direccion}: {e}")
        finally:
            cliente_sock.close()
    
    def _procesar_mensaje(self, mensaje: Dict) -> Dict:
        """Procesa un mensaje recibido"""
        try:
            tipo = mensaje.get('tipo')
            
            if tipo == 'sync_request':
                timestamp_desde = None
                if 'timestamp_desde' in mensaje and mensaje['timestamp_desde'] is not None:
                    ts_data = mensaje['timestamp_desde']
                    timestamp_desde = Timestamp(ts_data['node_id'], ts_data['counter'])
                
                actualizaciones = self.sincronizador.obtener_actualizaciones_desde(timestamp_desde)
                return {
                    'tipo': 'sync_response',
                    'datos': actualizaciones,
                    'exito': True
                }
            
            elif tipo == 'sync_data':
                self.sincronizador.aplicar_actualizaciones(mensaje['datos'])
                return {
                    'tipo': 'sync_ack',
                    'exito': True
                }
            
            else:
                return {
                    'tipo': 'error',
                    'mensaje': f'Tipo de mensaje desconocido: {tipo}',
                    'exito': False
                }
        
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}")
            return {
                'tipo': 'error',
                'mensaje': str(e),
                'exito': False
            }
    
    def _bucle_sincronizacion(self):
        """Bucle que ejecuta sincronización periódica"""
        while self.activo:
            try:
                time.sleep(3)  # Sincronizar cada 3 segundos para chat
                
                # Sincronizar con todos los nodos conectados
                for nodo_id in list(self.conexiones_activas.keys()):
                    self._sincronizar_con_nodo(nodo_id)
                    
            except Exception as e:
                self.logger.error(f"Error en bucle de sincronización: {e}")
    
    def _sincronizar_con_nodo(self, nodo_id: str):
        """Sincroniza con un nodo específico"""
        if nodo_id not in self.conexiones_activas:
            return
        
        try:
            sock = self.conexiones_activas[nodo_id]
            
            # Solicitar actualizaciones
            mensaje = {
                'tipo': 'sync_request',
                'timestamp_desde': self._serializar_timestamp(self.sincronizador.ultimo_sync_timestamp)
            }
            
            sock.send(json.dumps(mensaje).encode())
            
            # Recibir respuesta
            data = sock.recv(8192)
            respuesta = json.loads(data.decode())
            
            if respuesta.get('exito') and 'datos' in respuesta:
                self.sincronizador.aplicar_actualizaciones(respuesta['datos'])
                
                # Actualizar timestamp de última sincronización
                operaciones = respuesta['datos'].get('operaciones', [])
                if operaciones:
                    ultimo_ts = max(operaciones, key=lambda op: (op['timestamp']['node_id'], op['timestamp']['counter']))
                    self.sincronizador.ultimo_sync_timestamp = Timestamp(
                        ultimo_ts['timestamp']['node_id'],
                        ultimo_ts['timestamp']['counter']
                    )
            
        except Exception as e:
            self.logger.error(f"Error sincronizando con nodo {nodo_id}: {e}")
            # Eliminar conexión problemática
            if nodo_id in self.conexiones_activas:
                try:
                    self.conexiones_activas[nodo_id].close()
                except:
                    pass
                del self.conexiones_activas[nodo_id]
    
    def _serializar_timestamp(self, timestamp: Optional[Timestamp]) -> Optional[Dict]:
        """Serializa un timestamp a diccionario"""
        if timestamp is None:
            return None
        
        return {
            'node_id': timestamp.node_id,
            'counter': timestamp.counter
        }
    
    def obtener_nodos_descubiertos(self) -> List[InfoNodo]:
        """Obtiene la lista de nodos descubiertos"""
        return list(self.nodos_conocidos.values())
    
    def obtener_estadisticas_conexion(self) -> Dict[str, Any]:
        """Obtiene estadísticas de conexión"""
        return {
            'nodos_conocidos': len(self.nodos_conocidos),
            'conexiones_activas': len(self.conexiones_activas),
            'puerto_local': self.puerto,
            'usuario': self.nombre_usuario,
            'autodescubrimiento_activo': self.gestor_descubrimiento is not None
        }


def crear_cliente_simulado(nombre_usuario: str) -> ClienteP2PChat:
    """Crea un cliente simulado para pruebas"""
    chat = ChatCRDT(nombre_usuario)
    
    # Agregar mensaje inicial
    chat.enviar_mensaje(f"¡Hola! Soy {nombre_usuario} y me acabo de unir al chat.")
    
    cliente = ClienteP2PChat(chat, nombre_usuario, habilitar_autodescubrimiento=False)
    return cliente