"""
Sistema de sincronización para el crucigrama cooperativo
"""

import asyncio
import json
import uuid
import socket
import threading
import logging
from typing import Dict, Set, Optional, List
from dataclasses import asdict
from crucigrama_crdt import CrucigramaCRDT
from crdt_base import Operation, Timestamp
from descubrimiento_nodos import GestorDescubrimiento, TipoDescubrimiento, InfoNodo


class SincronizadorCrucigrama:
    """Maneja la sincronización entre diferentes instancias del crucigrama"""
    
    def __init__(self, crucigrama: CrucigramaCRDT):
        self.crucigrama = crucigrama
        self.clientes_conectados: Set[str] = set()
        self.ultimo_sync_timestamp: Optional[Timestamp] = None
        
    def registrar_cliente(self, cliente_id: str):
        """Registra un nuevo cliente"""
        self.clientes_conectados.add(cliente_id)
        
    def desregistrar_cliente(self, cliente_id: str):
        """Desregistra un cliente"""
        self.clientes_conectados.discard(cliente_id)
        
    def obtener_actualizaciones_desde(self, timestamp: Optional[Timestamp] = None) -> Dict:
        """Obtiene todas las operaciones desde un timestamp dado"""
        operaciones = self.crucigrama.obtener_operaciones_recientes(timestamp)
        
        return {
            'operaciones': [self._serializar_operacion(op) for op in operaciones],
            'estado_completo': self.crucigrama.obtener_estado_completo() if timestamp is None else None
        }
    
    def aplicar_actualizaciones(self, datos_sync: Dict):
        """Aplica actualizaciones recibidas de otros clientes"""
        if 'operaciones' in datos_sync:
            operaciones = [self._deserializar_operacion(op) for op in datos_sync['operaciones']]
            self.crucigrama.sincronizar_con(operaciones)
    
    def _serializar_operacion(self, operacion: Operation) -> Dict:
        """Convierte una operación a formato JSON"""
        return {
            'timestamp': {
                'node_id': operacion.timestamp.node_id,
                'counter': operacion.timestamp.counter
            },
            'operation_type': operacion.operation_type,
            'key': operacion.key,
            'value': {
                'letra': operacion.value.letra,
                'es_negra': operacion.value.es_negra,
                'numero': operacion.value.numero,
                'autor': operacion.value.autor
            } if hasattr(operacion.value, 'letra') else operacion.value,
            'author': operacion.author
        }
    
    def _deserializar_operacion(self, datos: Dict) -> Operation:
        """Convierte datos JSON a una operación"""
        from crucigrama_crdt import Celda
        
        timestamp = Timestamp(
            datos['timestamp']['node_id'],
            datos['timestamp']['counter']
        )
        
        # Reconstruir la celda si es necesario
        value = datos['value']
        if isinstance(value, dict) and 'letra' in value:
            value = Celda(
                letra=value['letra'],
                es_negra=value['es_negra'],
                numero=value['numero'],
                autor=value['autor']
            )
        
        return Operation(
            timestamp=timestamp,
            operation_type=datos['operation_type'],
            key=tuple(datos['key']),
            value=value,
            author=datos['author']
        )


class ClienteP2P:
    """Cliente para comunicación peer-to-peer entre crucigramas con autodescubrimiento"""
    
    def __init__(self, crucigrama: CrucigramaCRDT, puerto: int = 8765, 
                 nombre_usuario: str = None, habilitar_autodescubrimiento: bool = True):
        self.crucigrama = crucigrama
        self.sincronizador = SincronizadorCrucigrama(crucigrama)
        self.puerto = puerto
        self.peers: Dict[str, 'ClienteP2P'] = {}
        self.running = False
        self.nombre_usuario = nombre_usuario or crucigrama.node_id
        
        # Sistema de autodescubrimiento
        self.autodescubrimiento_habilitado = habilitar_autodescubrimiento
        self.gestor_descubrimiento = None
        self.conexiones_automaticas: Dict[str, bool] = {}  # Track de conexiones automáticas
        
        # Configurar logging
        self.logger = logging.getLogger(f"ClienteP2P-{self.crucigrama.node_id}")
        
        if self.autodescubrimiento_habilitado:
            self._configurar_autodescubrimiento()
    
    def conectar_peer(self, peer_id: str, peer: 'ClienteP2P'):
        """Conecta con otro peer"""
        self.peers[peer_id] = peer
        self.sincronizador.registrar_cliente(peer_id)
        
        # Intercambio inicial de estado
        actualizaciones = self.sincronizador.obtener_actualizaciones_desde()
        peer.recibir_actualizacion(self.crucigrama.node_id, actualizaciones)
    
    def desconectar_peer(self, peer_id: str):
        """Desconecta de un peer"""
        if peer_id in self.peers:
            del self.peers[peer_id]
            self.sincronizador.desregistrar_cliente(peer_id)
    
    def recibir_actualizacion(self, remitente_id: str, datos: Dict):
        """Recibe y aplica actualizaciones de un peer"""
        if remitente_id != self.crucigrama.node_id:
            self.sincronizador.aplicar_actualizaciones(datos)
            
            # Propagar a otros peers (excepto el remitente)
            for peer_id, peer in self.peers.items():
                if peer_id != remitente_id:
                    asyncio.create_task(self._enviar_actualizacion_async(peer, datos))
    
    async def _enviar_actualizacion_async(self, peer: 'ClienteP2P', datos: Dict):
        """Envía actualización de forma asíncrona"""
        try:
            peer.recibir_actualizacion(self.crucigrama.node_id, datos)
        except Exception as e:
            print(f"Error enviando actualización: {e}")
    
    def enviar_cambio_local(self):
        """Envía los cambios locales a todos los peers"""
        actualizaciones = self.sincronizador.obtener_actualizaciones_desde(
            self.sincronizador.ultimo_sync_timestamp
        )
        
        for peer in self.peers.values():
            peer.recibir_actualizacion(self.crucigrama.node_id, actualizaciones)
    
    def iniciar_sync_periodico(self, intervalo: float = 5.0):
        """Inicia sincronización periódica"""
        async def sync_loop():
            while self.running:
                try:
                    self.enviar_cambio_local()
                    await asyncio.sleep(intervalo)
                except Exception as e:
                    print(f"Error en sincronización periódica: {e}")
        
        self.running = True
        return asyncio.create_task(sync_loop())
    
    def detener_sync(self):
        """Detiene la sincronización"""
        self.running = False
        
        # Detener autodescubrimiento si está habilitado
        if self.gestor_descubrimiento:
            self.gestor_descubrimiento.detener_todos()
    
    def _configurar_autodescubrimiento(self):
        """Configura el sistema de autodescubrimiento"""
        self.gestor_descubrimiento = GestorDescubrimiento(
            self.crucigrama.node_id, 
            self.nombre_usuario
        )
        
        # Agregar algoritmos de descubrimiento
        self.gestor_descubrimiento.agregar_descubridor(
            TipoDescubrimiento.UDP_BROADCAST, 
            self.puerto
        )
        
        # Agregar callback para nodos descubiertos
        self.gestor_descubrimiento.agregar_callback_cambio(self._on_nodo_cambio)
        
        self.logger.info("Autodescubrimiento configurado")
    
    def iniciar_autodescubrimiento(self):
        """Inicia el sistema de autodescubrimiento"""
        if self.gestor_descubrimiento:
            self.gestor_descubrimiento.iniciar_todos()
            self.logger.info("Autodescubrimiento iniciado")
    
    def _on_nodo_cambio(self, tipo_cambio: str, nodo: InfoNodo):
        """Callback para cambios en nodos descubiertos"""
        if tipo_cambio == "descubierto":
            self._intentar_conexion_automatica(nodo)
        elif tipo_cambio == "perdido":
            self._manejar_nodo_perdido(nodo)
    
    def _intentar_conexion_automatica(self, nodo: InfoNodo):
        """Intenta conectar automáticamente con un nodo descubierto"""
        if nodo.node_id in self.conexiones_automaticas:
            return  # Ya intentamos conectar con este nodo
        
        self.conexiones_automaticas[nodo.node_id] = True
        
        try:
            # En una implementación real, aquí estableceríamos conexión TCP/WebSocket
            # Por ahora, simularemos la conexión
            self.logger.info(f"Conexión automática simulada con {nodo.nombre_usuario}")
            
            # Agregar el nodo a nuestro sincronizador
            self.sincronizador.registrar_cliente(nodo.node_id)
            
        except Exception as e:
            self.logger.error(f"Error conectando automáticamente con {nodo.node_id}: {e}")
    
    def _manejar_nodo_perdido(self, nodo: InfoNodo):
        """Maneja la pérdida de un nodo"""
        if nodo.node_id in self.conexiones_automaticas:
            del self.conexiones_automaticas[nodo.node_id]
        
        # Remover del sincronizador
        self.sincronizador.desregistrar_cliente(nodo.node_id)
        
        # Remover de peers si existe
        if nodo.node_id in self.peers:
            del self.peers[nodo.node_id]
        
        self.logger.info(f"Nodo {nodo.nombre_usuario} desconectado")
    
    def obtener_nodos_descubiertos(self) -> List[InfoNodo]:
        """Obtiene la lista de nodos descubiertos"""
        if self.gestor_descubrimiento:
            return self.gestor_descubrimiento.obtener_nodos()
        return []
    
    def obtener_estadisticas_descubrimiento(self) -> Dict:
        """Obtiene estadísticas del descubrimiento de nodos"""
        if self.gestor_descubrimiento:
            return self.gestor_descubrimiento.obtener_estadisticas()
        return {"error": "Autodescubrimiento no habilitado"}