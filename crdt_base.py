"""
Implementación base de CRDTs (Conflict-free Replicated Data Types)
"""

import time
import uuid
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Timestamp:
    """Timestamp vectorial para ordenamiento de operaciones"""
    node_id: str
    counter: int
    
    def __lt__(self, other):
        if self.counter != other.counter:
            return self.counter < other.counter
        return self.node_id < other.node_id
    
    def __eq__(self, other):
        return self.counter == other.counter and self.node_id == other.node_id


@dataclass
class Operation:
    """Operación en el CRDT"""
    timestamp: Timestamp
    operation_type: str
    key: Tuple[int, int]  # Posición (fila, columna)
    value: Any
    author: str


class CRDTMap:
    """
    CRDT tipo mapa para manejar el estado distribuido del crucigrama
    Utiliza Last Writer Wins con timestamps vectoriales
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.counter = 0
        self.data: Dict[Tuple[int, int], Any] = {}
        self.timestamps: Dict[Tuple[int, int], Timestamp] = {}
        self.operation_log = []
    
    def _generate_timestamp(self) -> Timestamp:
        """Genera un nuevo timestamp"""
        self.counter += 1
        return Timestamp(self.node_id, self.counter)
    
    def set(self, key: Tuple[int, int], value: Any, author: str) -> Operation:
        """Establece un valor en el mapa"""
        timestamp = self._generate_timestamp()
        operation = Operation(timestamp, "set", key, value, author)
        
        self._apply_operation(operation)
        return operation
    
    def get(self, key: Tuple[int, int]) -> Optional[Any]:
        """Obtiene un valor del mapa"""
        return self.data.get(key)
    
    def _apply_operation(self, operation: Operation):
        """Aplica una operación al estado local"""
        key = operation.key
        
        # Last Writer Wins: solo aplicar si el timestamp es más reciente
        if key not in self.timestamps or operation.timestamp > self.timestamps[key]:
            if operation.operation_type == "set":
                self.data[key] = operation.value
                self.timestamps[key] = operation.timestamp
        
        # Agregar al log de operaciones
        self.operation_log.append(operation)
    
    def merge(self, operations: list):
        """Merge operaciones desde otros nodos"""
        for operation in operations:
            if operation.timestamp.node_id != self.node_id:
                self._apply_operation(operation)
    
    def get_operations_since(self, timestamp: Optional[Timestamp] = None) -> list:
        """Obtiene operaciones desde un timestamp dado"""
        if timestamp is None:
            return self.operation_log.copy()
        
        return [op for op in self.operation_log if op.timestamp > timestamp]