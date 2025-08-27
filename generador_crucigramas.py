"""
Generador automático de crucigramas con diccionario de palabras y pistas
"""

import random
import json
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from crucigrama_crdt import CrucigramaCRDT


@dataclass
class PalabraPista:
    """Palabra con su pista correspondiente"""
    palabra: str
    pista: str
    categoria: str = "general"
    dificultad: int = 1  # 1=fácil, 5=difícil


class DiccionarioPalabras:
    """Diccionario de palabras con pistas por categorías"""
    
    def __init__(self):
        self.palabras: Dict[str, List[PalabraPista]] = {
            "tecnologia": [],
            "ciencia": [],
            "geografia": [],
            "historia": [],
            "cultura": [],
            "deportes": [],
            "general": []
        }
        self._cargar_diccionario_base()
    
    def _cargar_diccionario_base(self):
        """Carga diccionario base con palabras comunes"""
        
        # Tecnología
        tecnologia = [
            ("PYTHON", "Lenguaje de programación interpretado"),
            ("CRDT", "Tipo de dato replicado libre de conflictos"),
            ("JAVA", "Lenguaje de programación orientado a objetos"),
            ("HTML", "Lenguaje de marcado para páginas web"),
            ("LINUX", "Sistema operativo de código abierto"),
            ("GITHUB", "Plataforma de desarrollo colaborativo"),
            ("DOCKER", "Plataforma de contenedores"),
            ("NODEJS", "Entorno de ejecución de JavaScript"),
            ("REACT", "Biblioteca de JavaScript para interfaces"),
            ("MYSQL", "Sistema de gestión de bases de datos"),
            ("WIFI", "Tecnología de red inalámbrica"),
            ("CLOUD", "Computación en la nube"),
            ("API", "Interfaz de programación de aplicaciones"),
            ("JSON", "Formato de intercambio de datos"),
            ("HTTP", "Protocolo de transferencia de hipertexto"),
        ]
        
        for palabra, pista in tecnologia:
            self.palabras["tecnologia"].append(
                PalabraPista(palabra, pista, "tecnologia", 2)
            )
        
        # Ciencia
        ciencia = [
            ("ATOMO", "Unidad básica de la materia"),
            ("DNA", "Material genético de los seres vivos"),
            ("OXIGENO", "Elemento químico esencial para la respiración"),
            ("ELECTRON", "Partícula subatómica con carga negativa"),
            ("NEWTON", "Físico que formuló las leyes del movimiento"),
            ("EINSTEIN", "Científico de la teoría de la relatividad"),
            ("CARBON", "Elemento base de la química orgánica"),
            ("LASER", "Haz de luz concentrada y coherente"),
            ("QUANTUM", "Relacionado con la mecánica cuántica"),
            ("ENERGIA", "Capacidad para realizar trabajo"),
            ("DARWIN", "Naturalista de la teoría de la evolución"),
            ("CELULA", "Unidad básica de la vida"),
            ("PLASMA", "Cuarto estado de la materia"),
        ]
        
        for palabra, pista in ciencia:
            self.palabras["ciencia"].append(
                PalabraPista(palabra, pista, "ciencia", 3)
            )
        
        # Geografía
        geografia = [
            ("MADRID", "Capital de España"),
            ("AMAZON", "Río más largo de América del Sur"),
            ("SAHARA", "Desierto más grande de África"),
            ("EVEREST", "Montaña más alta del mundo"),
            ("NILO", "Río más largo del mundo"),
            ("EUROPA", "Continente donde está España"),
            ("PACIFICO", "Océano más grande del mundo"),
            ("ANDES", "Cordillera más larga del mundo"),
            ("TOKIO", "Capital de Japón"),
            ("ATLANTICO", "Océano entre Europa y América"),
            ("AFRICA", "Continente cuna de la humanidad"),
            ("HIMALAYA", "Cordillera donde está el Everest"),
        ]
        
        for palabra, pista in geografia:
            self.palabras["geografia"].append(
                PalabraPista(palabra, pista, "geografia", 2)
            )
        
        # Historia
        historia = [
            ("ROMA", "Imperio que dominó el Mediterráneo"),
            ("CESAR", "Emperador romano famoso"),
            ("NAPOLEON", "Emperador francés"),
            ("COLON", "Descubridor de América"),
            ("EGIPTO", "País de las pirámides"),
            ("VIKING", "Guerreros nórdicos navegantes"),
            ("AZTECA", "Civilización precolombina de México"),
            ("INCA", "Imperio andino precolombino"),
            ("SPARTA", "Ciudad estado guerrera de Grecia"),
            ("MEDIEVAL", "Época entre la antigua y moderna"),
        ]
        
        for palabra, pista in historia:
            self.palabras["historia"].append(
                PalabraPista(palabra, pista, "historia", 2)
            )
        
        # Cultura General
        general = [
            ("LIBRO", "Objeto para leer y aprender"),
            ("MUSICA", "Arte de los sonidos organizados"),
            ("ARTE", "Expresión creativa humana"),
            ("TEATRO", "Representación dramática en vivo"),
            ("CINE", "Arte audiovisual en movimiento"),
            ("PINTURA", "Arte de aplicar colores sobre superficie"),
            ("POETA", "Persona que escribe poesía"),
            ("NOVELA", "Obra literaria narrativa extensa"),
            ("OPERA", "Obra teatral cantada"),
            ("BALLET", "Danza clásica refinada"),
            ("VIOLIN", "Instrumento musical de cuerda"),
            ("PIANO", "Instrumento musical de teclas"),
            ("GUITARRA", "Instrumento de cuerda popular"),
        ]
        
        for palabra, pista in general:
            self.palabras["general"].append(
                PalabraPista(palabra, pista, "general", 1)
            )
        
        # Deportes
        deportes = [
            ("FUTBOL", "Deporte más popular del mundo"),
            ("TENNIS", "Deporte de raqueta individual"),
            ("BASKET", "Deporte de canasta alta"),
            ("GOLF", "Deporte de hoyos y palos"),
            ("NATACION", "Deporte acuático"),
            ("ATLETISMO", "Deporte de pista y campo"),
            ("CICLISMO", "Deporte sobre dos ruedas"),
            ("BOXEO", "Deporte de combate con guantes"),
            ("YOGA", "Práctica física y mental"),
            ("KARATE", "Arte marcial japonés"),
        ]
        
        for palabra, pista in deportes:
            self.palabras["deportes"].append(
                PalabraPista(palabra, pista, "deportes", 1)
            )
    
    def obtener_palabras_por_categoria(self, categoria: str) -> List[PalabraPista]:
        """Obtiene palabras de una categoría específica"""
        return self.palabras.get(categoria, [])
    
    def obtener_palabras_por_longitud(self, longitud: int, categoria: str = None) -> List[PalabraPista]:
        """Obtiene palabras de una longitud específica"""
        todas_palabras = []
        
        if categoria:
            todas_palabras = self.palabras.get(categoria, [])
        else:
            for cat_palabras in self.palabras.values():
                todas_palabras.extend(cat_palabras)
        
        return [p for p in todas_palabras if len(p.palabra) == longitud]
    
    def obtener_palabras_aleatorias(self, cantidad: int, categoria: str = None) -> List[PalabraPista]:
        """Obtiene palabras aleatorias"""
        todas_palabras = []
        
        if categoria:
            todas_palabras = self.palabras.get(categoria, [])
        else:
            for cat_palabras in self.palabras.values():
                todas_palabras.extend(cat_palabras)
        
        return random.sample(todas_palabras, min(cantidad, len(todas_palabras)))
    
    def buscar_palabra_que_contenga(self, letra: str, posicion: int, longitud: int) -> List[PalabraPista]:
        """Busca palabras que contengan una letra en posición específica"""
        resultado = []
        
        for cat_palabras in self.palabras.values():
            for palabra_pista in cat_palabras:
                palabra = palabra_pista.palabra
                if (len(palabra) == longitud and 
                    posicion < len(palabra) and 
                    palabra[posicion] == letra):
                    resultado.append(palabra_pista)
        
        return resultado


class GeneradorCrucigramas:
    """Generador automático de crucigramas"""
    
    def __init__(self, diccionario: DiccionarioPalabras = None):
        self.diccionario = diccionario or DiccionarioPalabras()
        self.max_intentos = 100
    
    def generar_crucigrama_basico(self, filas: int = 15, columnas: int = 15, 
                                 num_palabras: int = 8, categoria: str = None) -> CrucigramaCRDT:
        """Genera un crucigrama básico con palabras aleatorias"""
        crucigrama = CrucigramaCRDT(filas, columnas, "generador_auto")
        
        palabras_seleccionadas = self.diccionario.obtener_palabras_aleatorias(
            num_palabras * 2, categoria  # Obtener más palabras para tener opciones
        )
        
        palabras_colocadas = 0
        intentos = 0
        
        # Colocar primera palabra horizontal en el centro
        if palabras_seleccionadas:
            primera_palabra = palabras_seleccionadas[0]
            fila_centro = filas // 2
            col_inicio = (columnas - len(primera_palabra.palabra)) // 2
            
            if self._puede_colocar_palabra(crucigrama, primera_palabra.palabra, 
                                         fila_centro, col_inicio, "horizontal"):
                crucigrama.agregar_palabra(
                    primera_palabra.pista,
                    primera_palabra.palabra,
                    fila_centro,
                    col_inicio,
                    "horizontal",
                    "generador"
                )
                palabras_colocadas += 1
        
        # Colocar palabras restantes tratando de que se crucen
        for palabra_pista in palabras_seleccionadas[1:]:
            if palabras_colocadas >= num_palabras:
                break
            
            if self._colocar_palabra_con_cruces(crucigrama, palabra_pista):
                palabras_colocadas += 1
            
            intentos += 1
            if intentos > self.max_intentos:
                break
        
        return crucigrama
    
    def generar_crucigrama_tematico(self, tema: str, filas: int = 15, columnas: int = 15) -> CrucigramaCRDT:
        """Genera un crucigrama temático de una categoría específica"""
        return self.generar_crucigrama_basico(filas, columnas, 10, tema)
    
    def _puede_colocar_palabra(self, crucigrama: CrucigramaCRDT, palabra: str,
                              fila: int, columna: int, direccion: str) -> bool:
        """Verifica si se puede colocar una palabra en la posición"""
        return crucigrama._puede_colocar_palabra(palabra, fila, columna, direccion)
    
    def _colocar_palabra_con_cruces(self, crucigrama: CrucigramaCRDT, 
                                   palabra_pista: PalabraPista) -> bool:
        """Intenta colocar una palabra buscando cruces con palabras existentes"""
        palabra = palabra_pista.palabra
        
        # Obtener todas las celdas ocupadas
        celdas_ocupadas = []
        for fila in range(crucigrama.filas):
            for columna in range(crucigrama.columnas):
                celda = crucigrama.obtener_celda(fila, columna)
                if celda and celda.letra and not celda.es_negra:
                    celdas_ocupadas.append((fila, columna, celda.letra))
        
        # Intentar cruzar con cada letra existente
        for fila, columna, letra_existente in celdas_ocupadas:
            # Buscar si la nueva palabra contiene esta letra
            for i, letra in enumerate(palabra):
                if letra == letra_existente:
                    # Intentar colocar horizontal
                    nueva_col = columna - i
                    if (nueva_col >= 0 and 
                        nueva_col + len(palabra) <= crucigrama.columnas and
                        self._puede_colocar_palabra(crucigrama, palabra, fila, nueva_col, "horizontal")):
                        
                        crucigrama.agregar_palabra(
                            palabra_pista.pista,
                            palabra,
                            fila,
                            nueva_col,
                            "horizontal",
                            "generador"
                        )
                        return True
                    
                    # Intentar colocar vertical  
                    nueva_fila = fila - i
                    if (nueva_fila >= 0 and 
                        nueva_fila + len(palabra) <= crucigrama.filas and
                        self._puede_colocar_palabra(crucigrama, palabra, nueva_fila, columna, "vertical")):
                        
                        crucigrama.agregar_palabra(
                            palabra_pista.pista,
                            palabra,
                            nueva_fila,
                            columna,
                            "vertical",
                            "generador"
                        )
                        return True
        
        # Si no se puede cruzar, intentar colocar en posición aleatoria
        for _ in range(20):  # 20 intentos aleatorios
            fila = random.randint(0, crucigrama.filas - len(palabra))
            columna = random.randint(0, crucigrama.columnas - len(palabra))
            direccion = random.choice(["horizontal", "vertical"])
            
            if direccion == "vertical":
                fila = random.randint(0, crucigrama.filas - len(palabra))
                columna = random.randint(0, crucigrama.columnas - 1)
            
            if self._puede_colocar_palabra(crucigrama, palabra, fila, columna, direccion):
                crucigrama.agregar_palabra(
                    palabra_pista.pista,
                    palabra,
                    fila,
                    columna,
                    direccion,
                    "generador"
                )
                return True
        
        return False
    
    def generar_plantilla_facil(self) -> CrucigramaCRDT:
        """Genera una plantilla fácil con palabras cortas"""
        palabras_cortas = []
        for categoria in self.diccionario.palabras.values():
            palabras_cortas.extend([p for p in categoria if len(p.palabra) <= 6 and p.dificultad <= 2])
        
        crucigrama = CrucigramaCRDT(10, 10, "plantilla_facil")
        
        # Seleccionar palabras fáciles
        palabras_seleccionadas = random.sample(palabras_cortas, min(6, len(palabras_cortas)))
        
        for palabra_pista in palabras_seleccionadas:
            self._colocar_palabra_con_cruces(crucigrama, palabra_pista)
        
        return crucigrama
    
    def generar_plantilla_dificil(self) -> CrucigramaCRDT:
        """Genera una plantilla difícil con palabras técnicas"""
        palabras_dificiles = []
        for categoria in ["tecnologia", "ciencia"]:
            palabras_dificiles.extend(self.diccionario.palabras.get(categoria, []))
        
        return self.generar_crucigrama_basico(15, 15, 12, None)
    
    def guardar_crucigrama_json(self, crucigrama: CrucigramaCRDT, archivo: str):
        """Guarda un crucigrama en formato JSON"""
        estado = crucigrama.obtener_estado_completo()
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    
    def cargar_crucigrama_json(self, archivo: str, node_id: str = "cargado") -> CrucigramaCRDT:
        """Carga un crucigrama desde archivo JSON"""
        with open(archivo, 'r', encoding='utf-8') as f:
            estado = json.load(f)
        
        # Crear nuevo crucigrama
        crucigrama = CrucigramaCRDT(len(estado['grid']), len(estado['grid'][0]), node_id)
        
        # Cargar palabras
        for numero, datos_palabra in estado['palabras'].items():
            crucigrama.agregar_palabra(
                datos_palabra['pista'],
                datos_palabra['respuesta'], 
                datos_palabra['fila_inicio'],
                datos_palabra['columna_inicio'],
                datos_palabra['direccion'],
                datos_palabra['autor']
            )
        
        return crucigrama