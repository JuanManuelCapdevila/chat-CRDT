# Crucigrama Cooperativo con CRDTs

Un sistema de crucigrama colaborativo implementado en Python usando **Conflict-free Replicated Data Types (CRDTs)** para permitir que múltiples usuarios trabajen simultáneamente sin conflictos de sincronización.

## Características

- **Colaboración en tiempo real**: Múltiples usuarios pueden editar el mismo crucigrama simultáneamente
- **Resolución automática de conflictos**: Usa CRDTs con estrategia "Last Writer Wins"
- **Generación automática**: Crea crucigramas automáticamente con palabras y pistas
- **Autodescubrimiento de nodos**: Encuentra automáticamente otros usuarios en la red local
- **Sincronización P2P**: Los cambios se propagan automáticamente entre todos los clientes conectados
- **Interfaz gráfica moderna**: GUI intuitiva con tkinter para fácil interacción
- **Interfaz de línea de comandos**: Alternativa simple para interactuar por terminal
- **Persistencia de operaciones**: Todas las operaciones se almacenan para sincronización

## Estructura del Proyecto

```
crucigrama CRDT/
├── main.py              # Punto de entrada para línea de comandos
├── main_gui.py          # Punto de entrada para interfaz gráfica (widgets)
├── main_canvas.py       # Punto de entrada para interfaz Canvas (recomendado)
├── crucigrama_crdt.py   # Lógica principal del crucigrama con CRDT
├── crdt_base.py         # Implementación base de CRDTs
├── sincronizacion.py    # Sistema de sincronización P2P
├── cliente.py           # Interfaz de usuario en línea de comandos
├── gui_crucigrama.py    # Interfaz gráfica con widgets tkinter
├── gui_canvas.py        # Interfaz gráfica optimizada con Canvas
├── descubrimiento_nodos.py # Sistema de autodescubrimiento de nodos
├── generador_crucigramas.py # Generador automático de crucigramas
├── demo.py              # Demostraciones del sistema (CLI)
├── demo_gui.py          # Demostraciones con interfaz gráfica
├── demo_autodescubrimiento.py # Demos de autodescubrimiento
├── demo_generacion.py   # Demos de generación automática
├── requirements.txt     # Dependencias del proyecto
└── README.md           # Este archivo
```

## Instalación

1. Clona o descarga el proyecto
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Ejecución con Interfaz Gráfica

**Versión Canvas (Recomendado - Mejor rendimiento):**
```bash
python main_canvas.py
```

**Versión Clásica con Widgets:**
```bash
python main_gui.py
```

### Ejecución con Línea de Comandos
```bash
python main.py
```

### Demostraciones
```bash
# Demo con línea de comandos
python demo.py

# Demo con interfaz gráfica
python demo_gui.py

# Demo de autodescubrimiento de nodos
python demo_autodescubrimiento.py

# Demo de generación automática de crucigramas
python demo_generacion.py
```

## Funcionalidades

### Operaciones Básicas
- **Establecer letra**: Coloca una letra en una posición específica
- **Marcar celda negra**: Bloquea una celda (celdas sombreadas en crucigramas)
- **Agregar palabra**: Añade una palabra con su pista al crucigrama
- **Limpiar posición**: Borra el contenido de una celda

### Características Colaborativas
- **Sincronización automática**: Los cambios se propagan a todos los clientes conectados
- **Resolución de conflictos**: Si dos usuarios escriben en la misma posición, prevalece el último writer
- **Autoría**: Cada celda recuerda quién la modificó por última vez
- **Estado consistente**: Todos los clientes convergen al mismo estado final

## Arquitectura Técnica

### CRDTs (Conflict-free Replicated Data Types)
El sistema usa un **CRDT tipo mapa** con las siguientes características:
- **Last Writer Wins**: Resuelve conflictos basándose en timestamps vectoriales
- **Timestamps vectoriales**: Cada operación tiene un timestamp único (node_id + counter)
- **Convergencia eventual**: Todos los nodos alcanzan el mismo estado final
- **Tolerancia a particiones**: Funciona incluso con conectividad intermitente

### Componentes Principales

1. **CRDTMap** (`crdt_base.py`): Implementación base del CRDT
2. **CrucigramaCRDT** (`crucigrama_crdt.py`): Lógica específica del crucigrama
3. **SincronizadorCrucigrama** (`sincronizacion.py`): Manejo de sincronización
4. **ClienteP2P** (`sincronizacion.py`): Comunicación peer-to-peer

## Ejemplo de Uso

```python
from crucigrama_crdt import CrucigramaCRDT
from sincronizacion import ClienteP2P

# Crear crucigrama
crucigrama = CrucigramaCRDT(15, 15, "usuario1")

# Establecer letras
crucigrama.establecer_letra(2, 2, 'H', 'usuario1')
crucigrama.establecer_letra(2, 3, 'O', 'usuario1')

# Agregar palabra con pista
crucigrama.agregar_palabra(
    "Saludo común",
    "HOLA", 
    2, 2, "horizontal", 
    "usuario1"
)

# Configurar sincronización P2P
cliente = ClienteP2P(crucigrama)
```

## Demostraciones Incluidas

### Demo Básico
- Dos usuarios trabajando simultáneamente
- Sincronización automática de cambios
- Verificación de convergencia de estado

### Demo de Conflictos
- Escritura concurrente en la misma posición
- Resolución automática usando Last Writer Wins
- Convergencia a estado consistente

## Conceptos de CRDTs Implementados

- **Operaciones commutativas**: El orden de aplicación no afecta el resultado final
- **Idempotencia**: Aplicar la misma operación múltiples veces es seguro
- **Monotonía**: El estado solo puede "crecer", nunca retroceder
- **Convergencia eventual**: Todos los nodos alcanzan el mismo estado

## Limitaciones Actuales

- Sincronización P2P simulada (no hay red real)
- Interfaz básica de línea de comandos
- No hay persistencia en disco
- Estrategia simple de resolución de conflictos (Last Writer Wins)

## Características de la GUI

### Funcionalidades de la Interfaz Gráfica

**Versión Canvas (Recomendada)**:
- **Rendimiento optimizado**: Canvas único en lugar de widgets individuales
- **Interacción fluida**: Click, hover, navegación con teclado
- **Scroll inteligente**: Navegación automática a celdas seleccionadas
- **Visualización mejorada**: Colores y efectos visuales refinados
- **Responsive**: Se adapta automáticamente al tamaño de ventana

**Funcionalidades Comunes**:
- **Grid interactivo**: Click para escribir letras, click derecho para celdas negras
- **Panel de control**: Botones para todas las operaciones principales
- **Lista de palabras**: Visualización en tiempo real de palabras agregadas
- **Log de actividad**: Historial con timestamps de todas las acciones
- **Estadísticas en vivo**: Contador de palabras, celdas y nodos conectados
- **Diálogos intuitivos**: Formularios fáciles para agregar palabras
- **Actualización automática**: Sincronización visual en tiempo real
- **Identificación de autor**: Cada celda muestra quién la modificó

### Interacciones

**Canvas (Versión optimizada)**:
- **Click izquierdo**: Seleccionar celda (con efecto visual de selección)
- **Click derecho**: Marcar/desmarcar celda como negra
- **Teclado**: Escribir letras directamente, navegación con flechas
- **Hover**: Resaltado visual al pasar el mouse sobre celdas
- **Escape**: Deseleccionar celda actual
- **Scroll**: Rueda del mouse o scrollbars para navegar grid grande
- **Auto-scroll**: Se mueve automáticamente a la celda seleccionada

**Controles Generales**:
- **Botón "Agregar Palabra"**: Diálogo para crear palabras con pistas
- **Generación Automática**: Panel con botones para crear crucigramas por tema
- **Crucigrama Personalizado**: Diálogo para configurar generación a medida
- **Botones temáticos**: 🚀 Fácil, ⚡ Difícil, 💻 Tecnología, 🧪 Ciencia
- **Panel de ayuda**: Botón "?" con instrucciones completas

## Sistema de Autodescubrimiento de Nodos

### Algoritmos Implementados

1. **UDP Broadcast**: 
   - Envía broadcasts periódicos en la red local
   - Otros nodos escuchan y responden automáticamente
   - Detección rápida y eficiente en redes LAN

2. **Escaneo de Puertos**:
   - Escanea rangos de IP en la red local
   - Busca servicios activos en puertos específicos
   - Útil como respaldo cuando broadcast no funciona

### Características del Autodescubrimiento

- **Detección automática**: Los nodos se encuentran sin configuración manual
- **Conexión automática**: Se conectan automáticamente al descubrirse
- **Monitoreo de estado**: Detecta cuando los nodos se desconectan
- **Tolerancia a fallos**: Continúa funcionando aunque algunos nodos fallen
- **Múltiples algoritmos**: Usa varios métodos simultáneamente para mayor confiabilidad

### Uso del Autodescubrimiento

```python
from sincronizacion import ClienteP2P
from crucigrama_crdt import CrucigramaCRDT

# Crear crucigrama con autodescubrimiento habilitado
crucigrama = CrucigramaCRDT(15, 15, "mi_usuario")
cliente = ClienteP2P(
    crucigrama,
    nombre_usuario="Mi Usuario",
    habilitar_autodescubrimiento=True
)

# Iniciar autodescubrimiento
cliente.iniciar_autodescubrimiento()

# Obtener nodos descubiertos
nodos = cliente.obtener_nodos_descubiertos()
print(f"Encontrados {len(nodos)} nodos")
```

## Sistema de Generación Automática

### Características del Generador

- **Diccionario extenso**: Más de 100 palabras organizadas por categorías
- **Algoritmo inteligente**: Coloca palabras buscando cruces óptimos
- **Categorías temáticas**: Tecnología, Ciencia, Geografía, Historia, Deportes, Cultura General
- **Plantillas predefinidas**: Crucigramas fáciles y difíciles
- **Guardado/carga**: Formato JSON para persistencia

### Categorías Disponibles

1. **Tecnología**: Python, Java, HTML, Linux, Docker, etc.
2. **Ciencia**: Átomo, DNA, Einstein, Newton, etc.
3. **Geografía**: Madrid, Amazonas, Sahara, Everest, etc.
4. **Historia**: Roma, César, Napoleón, Colón, etc.
5. **Cultura General**: Arte, Música, Teatro, Literatura, etc.
6. **Deportes**: Fútbol, Tenis, Basketball, Golf, etc.

### Uso del Generador

```python
from generador_crucigramas import GeneradorCrucigramas

generador = GeneradorCrucigramas()

# Crucigrama básico (mixto)
crucigrama = generador.generar_crucigrama_basico(15, 15, 8)

# Crucigrama temático
crucigrama_tech = generador.generar_crucigrama_tematico("tecnologia")

# Plantillas predefinidas
crucigrama_facil = generador.generar_plantilla_facil()
crucigrama_dificil = generador.generar_plantilla_dificil()

# Guardar y cargar
generador.guardar_crucigrama_json(crucigrama, "mi_crucigrama.json")
crucigrama_cargado = generador.cargar_crucigrama_json("mi_crucigrama.json")
```

## Posibles Extensiones

- **Más algoritmos de descubrimiento**: mDNS, DHT, servidor central
- **Comunicación TCP real**: Reemplazar simulación con conexiones reales
- **Cifrado**: Comunicación segura entre nodos
- **Persistencia**: Guardar estado en base de datos
- **Autenticación**: Sistema de usuarios más robusto
- **Métricas**: Estadísticas de colaboración y rendimiento
- **Exportación**: Guardar crucigrama en formatos estándar
- **Temas**: Personalización visual de la interfaz