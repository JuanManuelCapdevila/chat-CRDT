"""
Crucigrama cooperativo usando CRDTs
"""

import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from crdt_base import CRDTMap, Operation


@dataclass
class Celda:
    """Representa una celda en el crucigrama"""
    letra: Optional[str] = None
    es_negra: bool = False
    numero: Optional[int] = None
    autor: Optional[str] = None


@dataclass
class Palabra:
    """Representa una palabra en el crucigrama"""
    numero: int
    pista: str
    respuesta: str
    fila_inicio: int
    columna_inicio: int
    direccion: str  # 'horizontal' o 'vertical'
    autor: str


class CrucigramaCRDT:
    """Crucigrama cooperativo basado en CRDTs"""
    
    def __init__(self, filas: int = 15, columnas: int = 15, node_id: str = None):
        self.filas = filas
        self.columnas = columnas
        self.node_id = node_id or str(uuid.uuid4())[:8]
        
        # CRDT para el estado de las celdas
        self.celdas_crdt = CRDTMap(self.node_id)
        
        # Estado local del crucigrama
        self.palabras: Dict[int, Palabra] = {}
        self.siguiente_numero = 1
        
        # Inicializar grid vacío
        self._inicializar_grid()
    
    def _inicializar_grid(self):
        """Inicializa el grid con celdas vacías"""
        for fila in range(self.filas):
            for columna in range(self.columnas):
                celda = Celda()
                self.celdas_crdt.set((fila, columna), celda, self.node_id)
    
    def establecer_letra(self, fila: int, columna: int, letra: str, autor: str) -> bool:
        """Establece una letra en una posición específica"""
        if not self._es_posicion_valida(fila, columna):
            return False
        
        celda_actual = self.celdas_crdt.get((fila, columna)) or Celda()
        
        if celda_actual.es_negra:
            return False
        
        nueva_celda = Celda(
            letra=letra.upper() if letra else None,
            es_negra=celda_actual.es_negra,
            numero=celda_actual.numero,
            autor=autor
        )
        
        self.celdas_crdt.set((fila, columna), nueva_celda, autor)
        return True
    
    def establecer_celda_negra(self, fila: int, columna: int, autor: str) -> bool:
        """Marca una celda como negra (bloqueda)"""
        if not self._es_posicion_valida(fila, columna):
            return False
        
        celda_actual = self.celdas_crdt.get((fila, columna)) or Celda()
        nueva_celda = Celda(
            letra=None,
            es_negra=True,
            numero=None,
            autor=autor
        )
        
        self.celdas_crdt.set((fila, columna), nueva_celda, autor)
        return True
    
    def agregar_palabra(self, pista: str, respuesta: str, fila_inicio: int, 
                       columna_inicio: int, direccion: str, autor: str) -> Optional[int]:
        """Agrega una nueva palabra al crucigrama"""
        respuesta = respuesta.upper().replace(" ", "")
        
        if not self._puede_colocar_palabra(respuesta, fila_inicio, columna_inicio, direccion):
            return None
        
        numero = self.siguiente_numero
        self.siguiente_numero += 1
        
        palabra = Palabra(
            numero=numero,
            pista=pista,
            respuesta=respuesta,
            fila_inicio=fila_inicio,
            columna_inicio=columna_inicio,
            direccion=direccion,
            autor=autor
        )
        
        self.palabras[numero] = palabra
        
        # Marcar celda de inicio con número
        celda_inicio = self.celdas_crdt.get((fila_inicio, columna_inicio)) or Celda()
        nueva_celda_inicio = Celda(
            letra=celda_inicio.letra,
            es_negra=False,
            numero=numero,
            autor=celda_inicio.autor
        )
        self.celdas_crdt.set((fila_inicio, columna_inicio), nueva_celda_inicio, autor)
        
        # Opcional: establecer las letras de la palabra
        for i, letra in enumerate(respuesta):
            if direccion == 'horizontal':
                self.establecer_letra(fila_inicio, columna_inicio + i, letra, autor)
            else:  # vertical
                self.establecer_letra(fila_inicio + i, columna_inicio, letra, autor)
        
        return numero
    
    def _puede_colocar_palabra(self, palabra: str, fila: int, columna: int, direccion: str) -> bool:
        """Verifica si se puede colocar una palabra en la posición dada"""
        longitud = len(palabra)
        
        if direccion == 'horizontal':
            if columna + longitud > self.columnas:
                return False
            for i in range(longitud):
                celda = self.celdas_crdt.get((fila, columna + i))
                if celda and celda.es_negra:
                    return False
        else:  # vertical
            if fila + longitud > self.filas:
                return False
            for i in range(longitud):
                celda = self.celdas_crdt.get((fila + i, columna))
                if celda and celda.es_negra:
                    return False
        
        return True
    
    def _es_posicion_valida(self, fila: int, columna: int) -> bool:
        """Verifica si la posición está dentro del grid"""
        return 0 <= fila < self.filas and 0 <= columna < self.columnas
    
    def obtener_celda(self, fila: int, columna: int) -> Optional[Celda]:
        """Obtiene la celda en una posición específica"""
        return self.celdas_crdt.get((fila, columna))
    
    def obtener_estado_completo(self) -> Dict:
        """Obtiene el estado completo del crucigrama"""
        grid = []
        for fila in range(self.filas):
            fila_celdas = []
            for columna in range(self.columnas):
                celda = self.obtener_celda(fila, columna)
                fila_celdas.append({
                    'letra': celda.letra if celda else None,
                    'es_negra': celda.es_negra if celda else False,
                    'numero': celda.numero if celda else None,
                    'autor': celda.autor if celda else None
                })
            grid.append(fila_celdas)
        
        return {
            'grid': grid,
            'palabras': {num: {
                'numero': p.numero,
                'pista': p.pista,
                'respuesta': p.respuesta,
                'fila_inicio': p.fila_inicio,
                'columna_inicio': p.columna_inicio,
                'direccion': p.direccion,
                'autor': p.autor
            } for num, p in self.palabras.items()}
        }
    
    def sincronizar_con(self, otras_operaciones: List[Operation]):
        """Sincroniza el estado con operaciones de otros nodos"""
        self.celdas_crdt.merge(otras_operaciones)
    
    def obtener_operaciones_recientes(self, desde_timestamp=None) -> List[Operation]:
        """Obtiene las operaciones recientes para sincronización"""
        return self.celdas_crdt.get_operations_since(desde_timestamp)