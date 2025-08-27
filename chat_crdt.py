#!/usr/bin/env python3
"""
Sistema de chat cooperativo usando CRDTs
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from crdt_base import CRDTMap, Timestamp, Operation


@dataclass
class Mensaje:
    """Representa un mensaje de chat"""
    mensaje_id: str
    contenido: str
    autor: str
    timestamp: datetime
    canal: str = "general"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'mensaje_id': self.mensaje_id,
            'contenido': self.contenido,
            'autor': self.autor,
            'timestamp': self.timestamp.isoformat(),
            'canal': self.canal
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mensaje':
        return cls(
            data['mensaje_id'],
            data['contenido'],
            data['autor'],
            datetime.fromisoformat(data['timestamp']),
            data['canal']
        )


@dataclass
class Operacion:
    """Operación específica para el chat"""
    tipo: str
    clave: str
    valor: Any
    timestamp: Timestamp
    usuario: str


class ChatCRDT:
    """
    Chat cooperativo implementado con CRDTs
    Permite múltiples usuarios chateando simultáneamente
    """
    
    def __init__(self, usuario_id: str):
        self.usuario_id = usuario_id
        self.crdt_map = CRDTMap(usuario_id)
        self.mensajes: Dict[str, Mensaje] = {}
        # CANAL ÚNICO - todos los mensajes van al canal "chat"
        self.canal_unico = "chat"
        self.canales: Dict[str, List[str]] = {self.canal_unico: []}
        self.usuarios_conectados: Dict[str, Dict[str, Any]] = {}
        self.callback_cambio = None
        self.operaciones_log: List[Operacion] = []
        
        # Para sincronización por estado
        self.vector_clock: Dict[str, int] = {usuario_id: 0}  # node_id -> counter
        self.ultimo_estado_hash: str = ""
        
    def establecer_callback_cambio(self, callback):
        """Establece callback para notificar cambios en la UI"""
        self.callback_cambio = callback
        
    def _notificar_cambio(self):
        """Notifica cambios a la UI si hay callback configurado"""
        if self.callback_cambio:
            self.callback_cambio()
    
    def enviar_mensaje(self, contenido: str, canal: str = None) -> str:
        """Envía un mensaje al chat - siempre al canal único"""
        # Incrementar vector clock
        self._incrementar_vector_clock()
        
        mensaje_id = str(uuid.uuid4())
        
        # TODOS los mensajes van al canal único
        mensaje = Mensaje(
            mensaje_id=mensaje_id,
            contenido=contenido,
            autor=self.usuario_id,
            timestamp=datetime.now(),
            canal=self.canal_unico  # Siempre usar canal único
        )
        
        # Aplicar localmente
        self.mensajes[mensaje_id] = mensaje
        self.canales[self.canal_unico].append(mensaje_id)
        
        # Crear operación CRDT (para compatibilidad)
        self.crdt_map.counter += 1
        operacion = Operacion(
            tipo="enviar_mensaje",
            clave=mensaje_id,
            valor=mensaje.to_dict(),
            timestamp=Timestamp(self.usuario_id, self.crdt_map.counter),
            usuario=self.usuario_id
        )
        
        # Guardar operación para sincronización
        self.operaciones_log.append(operacion)
        
        self._notificar_cambio()
        return mensaje_id
    
    def editar_mensaje(self, mensaje_id: str, nuevo_contenido: str) -> bool:
        """Edita un mensaje existente"""
        if mensaje_id not in self.mensajes:
            return False
        
        mensaje = self.mensajes[mensaje_id]
        
        # Solo el autor puede editar su mensaje
        if mensaje.autor != self.usuario_id:
            return False
        
        # Crear mensaje editado
        mensaje_editado = Mensaje(
            mensaje_id=mensaje_id,
            contenido=f"{nuevo_contenido} (editado)",
            autor=mensaje.autor,
            timestamp=mensaje.timestamp,  # Mantener timestamp original
            canal=mensaje.canal
        )
        
        # Crear operación CRDT
        self.crdt_map.counter += 1
        operacion = Operacion(
            tipo="editar_mensaje",
            clave=mensaje_id,
            valor=mensaje_editado.to_dict(),
            timestamp=Timestamp(self.usuario_id, self.crdt_map.counter),
            usuario=self.usuario_id
        )
        
        # Aplicar localmente
        self.mensajes[mensaje_id] = mensaje_editado
        
        # Guardar operación
        self.operaciones_log.append(operacion)
        
        self._notificar_cambio()
        return True
    
    def eliminar_mensaje(self, mensaje_id: str) -> bool:
        """Elimina un mensaje (soft delete)"""
        if mensaje_id not in self.mensajes:
            return False
        
        mensaje = self.mensajes[mensaje_id]
        
        # Solo el autor puede eliminar su mensaje
        if mensaje.autor != self.usuario_id:
            return False
        
        # Crear operación CRDT
        self.crdt_map.counter += 1
        operacion = Operacion(
            tipo="eliminar_mensaje",
            clave=mensaje_id,
            valor=None,
            timestamp=Timestamp(self.usuario_id, self.crdt_map.counter),
            usuario=self.usuario_id
        )
        
        # Marcar como eliminado
        mensaje_eliminado = Mensaje(
            mensaje_id=mensaje_id,
            contenido="[Mensaje eliminado]",
            autor=mensaje.autor,
            timestamp=mensaje.timestamp,
            canal=mensaje.canal
        )
        
        self.mensajes[mensaje_id] = mensaje_eliminado
        
        # Guardar operación
        self.operaciones_log.append(operacion)
        
        self._notificar_cambio()
        return True
    
    def crear_canal(self, nombre_canal: str) -> bool:
        """Crear canal - DESHABILITADO: Solo existe un canal único"""
        # En modo canal único, no se permiten canales nuevos
        return False
    
    def obtener_mensajes_canal(self, canal: str = None) -> List[Mensaje]:
        """Obtiene los mensajes del canal único ordenados por timestamp"""
        # Siempre usar el canal único, ignorar parámetro
        mensajes_canal = [self.mensajes[msg_id] for msg_id in self.canales[self.canal_unico] 
                         if msg_id in self.mensajes]
        
        # Ordenar por timestamp
        mensajes_canal.sort(key=lambda m: m.timestamp)
        return mensajes_canal
    
    def obtener_usuarios_activos(self) -> List[str]:
        """Obtiene la lista de usuarios que han enviado mensajes recientemente"""
        ahora = datetime.now()
        usuarios_activos = set()
        
        # Usuarios que han enviado mensajes en los últimos 10 minutos
        for mensaje in self.mensajes.values():
            if (ahora - mensaje.timestamp).total_seconds() < 600:  # 10 minutos
                usuarios_activos.add(mensaje.autor)
        
        return list(usuarios_activos)
    
    def buscar_mensajes(self, query: str) -> List[Mensaje]:
        """Busca mensajes que contengan el texto especificado"""
        query = query.lower()
        resultados = []
        
        for mensaje in self.mensajes.values():
            if query in mensaje.contenido.lower() or query in mensaje.autor.lower():
                resultados.append(mensaje)
        
        # Ordenar por relevancia y timestamp
        resultados.sort(key=lambda m: (
            -m.contenido.lower().count(query),  # Más ocurrencias primero
            -m.timestamp.timestamp()  # Más recientes primero
        ))
        
        return resultados
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del chat"""
        mensajes_hoy = 0
        ahora = datetime.now()
        
        for mensaje in self.mensajes.values():
            if (ahora - mensaje.timestamp).days == 0:
                mensajes_hoy += 1
        
        return {
            'total_mensajes': len(self.mensajes),
            'mensajes_hoy': mensajes_hoy,
            'canales_activos': len(self.canales),
            'usuarios_activos': len(self.obtener_usuarios_activos()),
            'usuarios_conectados': len(self.usuarios_conectados)
        }
    
    def aplicar_operacion_remota(self, operacion: Operacion):
        """Aplica una operación recibida de otro nodo"""
        # Verificar si ya tenemos esta operación
        for op_existente in self.operaciones_log:
            if (op_existente.timestamp.node_id == operacion.timestamp.node_id and 
                op_existente.timestamp.counter == operacion.timestamp.counter):
                return False  # Ya aplicada
        
        # Aplicar según el tipo de operación
        if operacion.tipo == "enviar_mensaje":
            mensaje_data = operacion.valor
            mensaje = Mensaje.from_dict(mensaje_data)
            self.mensajes[operacion.clave] = mensaje
            
            canal = mensaje.canal
            if canal not in self.canales:
                self.canales[canal] = []
            if operacion.clave not in self.canales[canal]:
                self.canales[canal].append(operacion.clave)
                
        elif operacion.tipo == "editar_mensaje":
            if operacion.clave in self.mensajes:
                mensaje_data = operacion.valor
                mensaje = Mensaje.from_dict(mensaje_data)
                self.mensajes[operacion.clave] = mensaje
                
        elif operacion.tipo == "eliminar_mensaje":
            if operacion.clave in self.mensajes:
                mensaje_original = self.mensajes[operacion.clave]
                mensaje_eliminado = Mensaje(
                    mensaje_id=operacion.clave,
                    contenido="[Mensaje eliminado]",
                    autor=mensaje_original.autor,
                    timestamp=mensaje_original.timestamp,
                    canal=mensaje_original.canal
                )
                self.mensajes[operacion.clave] = mensaje_eliminado
                
        elif operacion.tipo == "crear_canal":
            if operacion.clave not in self.canales:
                self.canales[operacion.clave] = []
        
        # Agregar operación al log
        self.operaciones_log.append(operacion)
        
        self._notificar_cambio()
        return True
    
    def obtener_operaciones(self) -> List[Operacion]:
        """Obtiene todas las operaciones para sincronización"""
        return self.operaciones_log.copy()
    
    def sincronizar_con(self, otras_operaciones: List[Operacion]):
        """Sincroniza con operaciones de otro nodo"""
        cambios = False
        for operacion in otras_operaciones:
            if self.aplicar_operacion_remota(operacion):
                cambios = True
        
        if cambios:
            self._notificar_cambio()
    
    def obtener_mensajes_ordenados(self, limite: int = 100) -> List[Mensaje]:
        """Obtiene los mensajes más recientes ordenados por timestamp"""
        mensajes = list(self.mensajes.values())
        mensajes.sort(key=lambda m: m.timestamp, reverse=True)
        return mensajes[:limite]
    
    def exportar_chat(self) -> Dict[str, Any]:
        """Exporta todo el chat a un diccionario"""
        return {
            'usuario_id': self.usuario_id,
            'mensajes': {mid: msg.to_dict() for mid, msg in self.mensajes.items()},
            'canales': self.canales,
            'timestamp_exportacion': datetime.now().isoformat(),
            'estadisticas': self.obtener_estadisticas()
        }
    
    def obtener_estado_completo(self) -> Dict[str, Any]:
        """Obtiene el estado completo del chat para sincronización"""
        return {
            'usuario_id': self.usuario_id,
            'vector_clock': self.vector_clock.copy(),
            'mensajes': {mid: msg.to_dict() for mid, msg in self.mensajes.items()},
            'canales': self.canales.copy(),
            'timestamp': datetime.now().timestamp()
        }
    
    def sincronizar_por_estado(self, estado_remoto: Dict[str, Any]) -> bool:
        """Sincroniza usando el estado completo de otro nodo"""
        cambios_realizados = False
        usuario_remoto = estado_remoto.get('usuario_id')
        vector_clock_remoto = estado_remoto.get('vector_clock', {})
        mensajes_remotos = estado_remoto.get('mensajes', {})
        canales_remotos = estado_remoto.get('canales', {})
        
        # Actualizar vector clock
        for node_id, counter in vector_clock_remoto.items():
            if node_id not in self.vector_clock:
                self.vector_clock[node_id] = 0
            
            if counter > self.vector_clock[node_id]:
                self.vector_clock[node_id] = counter
                cambios_realizados = True
        
        # Sincronizar mensajes usando Last Writer Wins
        for mensaje_id, mensaje_data in mensajes_remotos.items():
            mensaje_remoto = Mensaje.from_dict(mensaje_data)
            
            if mensaje_id not in self.mensajes:
                # Mensaje nuevo - SIEMPRE va al canal único
                mensaje_remoto.canal = self.canal_unico  # Forzar canal único
                self.mensajes[mensaje_id] = mensaje_remoto
                
                # Agregar al canal único
                if mensaje_id not in self.canales[self.canal_unico]:
                    self.canales[self.canal_unico].append(mensaje_id)
                
                cambios_realizados = True
                
            else:
                # Mensaje existente - comparar timestamps
                mensaje_local = self.mensajes[mensaje_id]
                
                if mensaje_remoto.timestamp > mensaje_local.timestamp:
                    # El mensaje remoto es más reciente
                    mensaje_remoto.canal = self.canal_unico  # Forzar canal único
                    self.mensajes[mensaje_id] = mensaje_remoto
                    cambios_realizados = True
        
        # Sincronizar canales - Solo el canal único
        # Agregar todos los mensajes remotos al canal único
        for mensaje_id in self.mensajes.keys():
            if mensaje_id not in self.canales[self.canal_unico]:
                self.canales[self.canal_unico].append(mensaje_id)
                cambios_realizados = True
        
        if cambios_realizados:
            self._notificar_cambio()
            
        return cambios_realizados
    
    def _incrementar_vector_clock(self):
        """Incrementa el vector clock local"""
        self.vector_clock[self.usuario_id] = self.vector_clock.get(self.usuario_id, 0) + 1