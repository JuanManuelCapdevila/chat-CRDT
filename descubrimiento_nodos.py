"""
Sistema de autodescubrimiento de nodos para crucigrama cooperativo
Implementa diferentes algoritmos para encontrar nodos cercanos en la red
"""

import socket
import threading
import time
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Tuple, Callable, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TipoDescubrimiento(Enum):
    """Tipos de algoritmos de descubrimiento disponibles"""
    UDP_BROADCAST = "udp_broadcast"
    MULTICAST = "multicast"
    MDNS = "mdns"
    SCAN_PUERTOS = "port_scan"


@dataclass
class InfoNodo:
    """Información de un nodo descubierto"""
    node_id: str
    nombre_usuario: str
    ip_address: str
    puerto: int
    timestamp: float
    version_protocolo: str = "1.0"
    tipo_aplicacion: str = "crucigrama_crdt"
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class DescubridorNodos:
    """Clase base para algoritmos de descubrimiento de nodos"""
    
    def __init__(self, node_id: str, nombre_usuario: str, puerto_base: int = 12345):
        self.node_id = node_id
        self.nombre_usuario = nombre_usuario
        self.puerto_base = puerto_base
        self.puerto_escucha = puerto_base
        self.nodos_descubiertos: Dict[str, InfoNodo] = {}
        self.callbacks_descubrimiento: List[Callable] = []
        self.callbacks_perdida: List[Callable] = []
        self.activo = False
        self.hilo_escucha = None
        self.hilo_anuncio = None
        
        # Configurar logging
        self.logger = logging.getLogger(f"Descubridor-{node_id}")
    
    def agregar_callback_descubrimiento(self, callback: Callable[[InfoNodo], None]):
        """Agrega callback para cuando se descubre un nodo"""
        self.callbacks_descubrimiento.append(callback)
    
    def agregar_callback_perdida(self, callback: Callable[[InfoNodo], None]):
        """Agrega callback para cuando se pierde un nodo"""
        self.callbacks_perdida.append(callback)
    
    def _notificar_descubrimiento(self, nodo: InfoNodo):
        """Notifica el descubrimiento de un nodo"""
        for callback in self.callbacks_descubrimiento:
            try:
                callback(nodo)
            except Exception as e:
                self.logger.error(f"Error en callback descubrimiento: {e}")
    
    def _notificar_perdida(self, nodo: InfoNodo):
        """Notifica la pérdida de un nodo"""
        for callback in self.callbacks_perdida:
            try:
                callback(nodo)
            except Exception as e:
                self.logger.error(f"Error en callback pérdida: {e}")
    
    def iniciar(self):
        """Inicia el servicio de descubrimiento"""
        raise NotImplementedError
    
    def detener(self):
        """Detiene el servicio de descubrimiento"""
        self.activo = False
        if self.hilo_escucha:
            self.hilo_escucha.join(timeout=2)
        if self.hilo_anuncio:
            self.hilo_anuncio.join(timeout=2)
    
    def obtener_nodos(self) -> List[InfoNodo]:
        """Obtiene la lista de nodos descubiertos"""
        return list(self.nodos_descubiertos.values())


class DescubridorUDPBroadcast(DescubridorNodos):
    """Descubrimiento usando UDP broadcast en red local"""
    
    def __init__(self, node_id: str, nombre_usuario: str, puerto_base: int = 12345):
        super().__init__(node_id, nombre_usuario, puerto_base)
        self.puerto_broadcast = puerto_base + 1000
        self.broadcast_interval = 10.0  # Anunciar cada 10 segundos
        self.timeout_nodo = 30.0  # Considerar nodo perdido después de 30s
    
    def iniciar(self):
        """Inicia el servicio UDP broadcast"""
        self.activo = True
        
        # Iniciar hilo de escucha
        self.hilo_escucha = threading.Thread(target=self._escuchar_broadcasts, daemon=True)
        self.hilo_escucha.start()
        
        # Iniciar hilo de anuncio
        self.hilo_anuncio = threading.Thread(target=self._enviar_broadcasts, daemon=True)
        self.hilo_anuncio.start()
        
        # Iniciar hilo de limpieza de nodos inactivos
        self.hilo_limpieza = threading.Thread(target=self._limpiar_nodos_inactivos, daemon=True)
        self.hilo_limpieza.start()
        
        self.logger.info(f"Servicio UDP broadcast iniciado en puerto {self.puerto_broadcast}")
    
    def _escuchar_broadcasts(self):
        """Escucha broadcasts de otros nodos"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.puerto_broadcast))
            sock.settimeout(1.0)
            
            while self.activo:
                try:
                    data, addr = sock.recvfrom(1024)
                    self._procesar_broadcast(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Error recibiendo broadcast: {e}")
        
        except Exception as e:
            self.logger.error(f"Error configurando socket escucha: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
    
    def _enviar_broadcasts(self):
        """Envía broadcasts periódicos anunciando este nodo"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            while self.activo:
                mensaje = self._crear_mensaje_anuncio()
                try:
                    sock.sendto(mensaje.encode('utf-8'), ('<broadcast>', self.puerto_broadcast))
                    self.logger.debug(f"Broadcast enviado: {self.node_id}")
                except Exception as e:
                    self.logger.error(f"Error enviando broadcast: {e}")
                
                time.sleep(self.broadcast_interval)
        
        except Exception as e:
            self.logger.error(f"Error configurando socket broadcast: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
    
    def _crear_mensaje_anuncio(self) -> str:
        """Crea mensaje de anuncio JSON"""
        info = InfoNodo(
            node_id=self.node_id,
            nombre_usuario=self.nombre_usuario,
            ip_address=self._obtener_ip_local(),
            puerto=self.puerto_escucha,
            timestamp=time.time()
        )
        return json.dumps(info.to_dict())
    
    def _procesar_broadcast(self, data: bytes, addr: Tuple[str, int]):
        """Procesa un broadcast recibido"""
        try:
            mensaje = json.loads(data.decode('utf-8'))
            info_nodo = InfoNodo.from_dict(mensaje)
            
            # Ignorar nuestros propios broadcasts
            if info_nodo.node_id == self.node_id:
                return
            
            # Verificar si es un nodo nuevo o actualización
            if info_nodo.node_id not in self.nodos_descubiertos:
                self.logger.info(f"Nuevo nodo descubierto: {info_nodo.nombre_usuario} ({info_nodo.node_id})")
                self.nodos_descubiertos[info_nodo.node_id] = info_nodo
                self._notificar_descubrimiento(info_nodo)
            else:
                # Actualizar timestamp del nodo existente
                self.nodos_descubiertos[info_nodo.node_id].timestamp = info_nodo.timestamp
        
        except Exception as e:
            self.logger.error(f"Error procesando broadcast de {addr}: {e}")
    
    def _limpiar_nodos_inactivos(self):
        """Limpia nodos que no han enviado broadcasts recientemente"""
        while self.activo:
            time.sleep(5)  # Revisar cada 5 segundos
            
            tiempo_actual = time.time()
            nodos_a_eliminar = []
            
            for node_id, info_nodo in self.nodos_descubiertos.items():
                if tiempo_actual - info_nodo.timestamp > self.timeout_nodo:
                    nodos_a_eliminar.append(node_id)
            
            for node_id in nodos_a_eliminar:
                nodo_perdido = self.nodos_descubiertos.pop(node_id)
                self.logger.info(f"Nodo perdido: {nodo_perdido.nombre_usuario} ({node_id})")
                self._notificar_perdida(nodo_perdido)
    
    def _obtener_ip_local(self) -> str:
        """Obtiene la IP local de este nodo"""
        try:
            # Conectar a un servidor remoto para obtener IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"


class DescubridorEscanPuertos(DescubridorNodos):
    """Descubrimiento mediante escaneo de puertos en red local"""
    
    def __init__(self, node_id: str, nombre_usuario: str, puerto_base: int = 12345):
        super().__init__(node_id, nombre_usuario, puerto_base)
        self.puerto_servicio = puerto_base + 2000
        self.intervalo_escaneo = 30.0  # Escanear cada 30 segundos
        self.timeout_conexion = 2.0
    
    def iniciar(self):
        """Inicia el servicio de escucha y escaneo"""
        self.activo = True
        
        # Iniciar servidor de identificación
        self.hilo_escucha = threading.Thread(target=self._ejecutar_servidor, daemon=True)
        self.hilo_escucha.start()
        
        # Iniciar escaneo periódico
        self.hilo_anuncio = threading.Thread(target=self._escanear_periodicamente, daemon=True)
        self.hilo_anuncio.start()
        
        self.logger.info(f"Servicio de escaneo iniciado en puerto {self.puerto_servicio}")
    
    def _ejecutar_servidor(self):
        """Ejecuta servidor para responder a sondeos"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('', self.puerto_servicio))
            server_socket.listen(5)
            server_socket.settimeout(1.0)
            
            while self.activo:
                try:
                    client_socket, addr = server_socket.accept()
                    self._manejar_conexion_cliente(client_socket, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Error aceptando conexión: {e}")
        
        except Exception as e:
            self.logger.error(f"Error iniciando servidor: {e}")
        finally:
            try:
                server_socket.close()
            except:
                pass
    
    def _manejar_conexion_cliente(self, client_socket: socket.socket, addr: Tuple[str, int]):
        """Maneja conexión entrante de otro nodo"""
        try:
            with client_socket:
                # Enviar nuestra información
                info = InfoNodo(
                    node_id=self.node_id,
                    nombre_usuario=self.nombre_usuario,
                    ip_address=self._obtener_ip_local(),
                    puerto=self.puerto_servicio,
                    timestamp=time.time()
                )
                
                mensaje = json.dumps(info.to_dict())
                client_socket.send(mensaje.encode('utf-8'))
        
        except Exception as e:
            self.logger.error(f"Error manejando cliente {addr}: {e}")
    
    def _escanear_periodicamente(self):
        """Escanea la red local periódicamente"""
        while self.activo:
            self._escanear_red_local()
            time.sleep(self.intervalo_escaneo)
    
    def _escanear_red_local(self):
        """Escanea la red local buscando otros nodos"""
        ip_local = self._obtener_ip_local()
        red_base = '.'.join(ip_local.split('.')[:-1]) + '.'
        
        # Escanear rango de IPs en paralelo
        hilos = []
        for i in range(1, 255):
            ip_target = red_base + str(i)
            if ip_target != ip_local:  # No escanear nuestra propia IP
                hilo = threading.Thread(
                    target=self._probar_ip, 
                    args=(ip_target,), 
                    daemon=True
                )
                hilo.start()
                hilos.append(hilo)
        
        # Esperar a que terminen los escaneos (con timeout)
        for hilo in hilos:
            hilo.join(timeout=0.1)
    
    def _probar_ip(self, ip: str):
        """Prueba si hay un nodo en la IP especificada"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout_conexion)
            
            resultado = sock.connect_ex((ip, self.puerto_servicio))
            if resultado == 0:
                # Conexión exitosa, obtener información del nodo
                data = sock.recv(1024)
                if data:
                    info_nodo = InfoNodo.from_dict(json.loads(data.decode('utf-8')))
                    
                    if info_nodo.node_id != self.node_id:  # Ignorar nosotros mismos
                        if info_nodo.node_id not in self.nodos_descubiertos:
                            self.logger.info(f"Nodo encontrado por escaneo: {info_nodo.nombre_usuario}")
                            self.nodos_descubiertos[info_nodo.node_id] = info_nodo
                            self._notificar_descubrimiento(info_nodo)
            
            sock.close()
        
        except Exception:
            # Es normal que la mayoría de IPs no tengan el servicio
            pass
    
    def _obtener_ip_local(self) -> str:
        """Obtiene la IP local de este nodo"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"


class GestorDescubrimiento:
    """Gestor principal para coordinar diferentes algoritmos de descubrimiento"""
    
    def __init__(self, node_id: str, nombre_usuario: str):
        self.node_id = node_id
        self.nombre_usuario = nombre_usuario
        self.descubridores: Dict[TipoDescubrimiento, DescubridorNodos] = {}
        self.nodos_consolidados: Dict[str, InfoNodo] = {}
        self.callbacks_cambio: List[Callable] = []
        
        self.logger = logging.getLogger(f"GestorDescubrimiento-{node_id}")
    
    def agregar_descubridor(self, tipo: TipoDescubrimiento, puerto_base: int = 12345):
        """Agrega un algoritmo de descubrimiento"""
        if tipo == TipoDescubrimiento.UDP_BROADCAST:
            descubridor = DescubridorUDPBroadcast(self.node_id, self.nombre_usuario, puerto_base)
        elif tipo == TipoDescubrimiento.SCAN_PUERTOS:
            descubridor = DescubridorEscanPuertos(self.node_id, self.nombre_usuario, puerto_base)
        else:
            raise ValueError(f"Tipo de descubrimiento no implementado: {tipo}")
        
        # Configurar callbacks
        descubridor.agregar_callback_descubrimiento(self._on_nodo_descubierto)
        descubridor.agregar_callback_perdida(self._on_nodo_perdido)
        
        self.descubridores[tipo] = descubridor
        self.logger.info(f"Descubridor {tipo.value} agregado")
    
    def iniciar_todos(self):
        """Inicia todos los descubridores configurados"""
        for descubridor in self.descubridores.values():
            descubridor.iniciar()
        
        self.logger.info(f"Iniciados {len(self.descubridores)} descubridores")
    
    def detener_todos(self):
        """Detiene todos los descubridores"""
        for descubridor in self.descubridores.values():
            descubridor.detener()
        
        self.logger.info("Todos los descubridores detenidos")
    
    def _on_nodo_descubierto(self, nodo: InfoNodo):
        """Callback cuando se descubre un nodo"""
        if nodo.node_id not in self.nodos_consolidados:
            self.nodos_consolidados[nodo.node_id] = nodo
            self.logger.info(f"Nuevo nodo consolidado: {nodo.nombre_usuario}")
            
            # Notificar a callbacks
            for callback in self.callbacks_cambio:
                try:
                    callback("descubierto", nodo)
                except Exception as e:
                    self.logger.error(f"Error en callback cambio: {e}")
    
    def _on_nodo_perdido(self, nodo: InfoNodo):
        """Callback cuando se pierde un nodo"""
        if nodo.node_id in self.nodos_consolidados:
            del self.nodos_consolidados[nodo.node_id]
            self.logger.info(f"Nodo perdido: {nodo.nombre_usuario}")
            
            # Notificar a callbacks
            for callback in self.callbacks_cambio:
                try:
                    callback("perdido", nodo)
                except Exception as e:
                    self.logger.error(f"Error en callback cambio: {e}")
    
    def agregar_callback_cambio(self, callback: Callable[[str, InfoNodo], None]):
        """Agrega callback para cambios en nodos (descubierto/perdido)"""
        self.callbacks_cambio.append(callback)
    
    def obtener_nodos(self) -> List[InfoNodo]:
        """Obtiene todos los nodos descubiertos"""
        return list(self.nodos_consolidados.values())
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de descubrimiento"""
        stats = {
            "nodos_totales": len(self.nodos_consolidados),
            "descubridores_activos": len(self.descubridores),
            "nodos_por_descubridor": {}
        }
        
        for tipo, descubridor in self.descubridores.items():
            stats["nodos_por_descubridor"][tipo.value] = len(descubridor.obtener_nodos())
        
        return stats