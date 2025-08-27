# Chat Cooperativo con CRDTs

Un sistema de chat colaborativo implementado en Python usando **Conflict-free Replicated Data Types (CRDTs)** para permitir que múltiples usuarios chateen simultáneamente con autodescubrimiento automático de nodos y lista de participantes en tiempo real.

## Características

- **Chat en tiempo real**: Múltiples usuarios pueden chatear simultáneamente sin conflictos
- **Autodescubrimiento automático**: Encuentra automáticamente otros usuarios en la red local
- **Lista de nodos en vivo**: Visualización en tiempo real de usuarios conectados y desconectados
- **Múltiples canales**: Crea y participa en diferentes canales temáticos
- **Resolución automática de conflictos**: Usa CRDTs con estrategia "Last Writer Wins"
- **Sincronización P2P**: Los mensajes se propagan automáticamente entre todos los clientes
- **Edición de mensajes**: Edita y elimina tus propios mensajes
- **Búsqueda avanzada**: Busca mensajes por contenido o autor
- **Interfaz moderna**: GUI intuitiva con lista de nodos, canales y estadísticas

## Estructura del Proyecto

```
crucigrama CRDT/
├── main_chat.py         # Punto de entrada principal para el chat
├── chat_crdt.py         # Lógica principal del chat con CRDT
├── gui_chat.py          # Interfaz gráfica del chat con lista de nodos
├── sincronizacion_chat.py # Sistema de sincronización P2P para chat
├── demo_chat.py         # Demostraciones del chat cooperativo
├── crdt_base.py         # Implementación base de CRDTs
├── descubrimiento_nodos.py # Sistema de autodescubrimiento de nodos
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

### Chat Cooperativo

**Interfaz gráfica del chat:**
```bash
python main_chat.py
```

**Demostraciones del chat:**
```bash
python demo_chat.py
```

### Funcionalidades Principales

1. **Inicia la aplicación** y ingresa tu nombre de usuario
2. **Visualiza nodos conectados** en el panel izquierdo en tiempo real
3. **Crea canales** para conversaciones temáticas
4. **Envía mensajes** que se sincronizan automáticamente
5. **Edita/elimina** tus propios mensajes
6. **Busca** en el historial de conversaciones

## Funcionalidades del Chat

### Operaciones Básicas
- **Enviar mensajes**: Escribir mensajes que se sincronizan en tiempo real
- **Crear canales**: Organizar conversaciones por temas
- **Editar mensajes**: Modificar tus propios mensajes (solo autor)
- **Eliminar mensajes**: Remover mensajes propios (soft delete)
- **Buscar mensajes**: Encontrar mensajes por contenido o autor
- **Ver estadísticas**: Métricas de actividad y participación

### Lista de Nodos en Tiempo Real
- **Autodescubrimiento**: Encuentra automáticamente usuarios cercanos
- **Estado de conexión**: Visualiza quién está conectado/desconectado
- **Información detallada**: IP, puerto, metadatos de cada nodo
- **Conexiones P2P**: Se conecta automáticamente a nodos descubiertos
- **Tolerancia a fallos**: Maneja desconexiones y reconexiones

## Arquitectura Técnica

### CRDTs (Conflict-free Replicated Data Types)
El sistema usa un **CRDT tipo mapa** con las siguientes características:
- **Last Writer Wins**: Resuelve conflictos basándose en timestamps vectoriales
- **Timestamps vectoriales**: Cada operación tiene un timestamp único (node_id + counter)
- **Convergencia eventual**: Todos los nodos alcanzan el mismo estado final
- **Tolerancia a particiones**: Funciona incluso con conectividad intermitente

### Componentes Principales

1. **CRDTMap** (`crdt_base.py`): Implementación base del CRDT
2. **ChatCRDT** (`chat_crdt.py`): Lógica específica del chat cooperativo
3. **SincronizadorChat** (`sincronizacion_chat.py`): Manejo de sincronización del chat
4. **ClienteP2PChat** (`sincronizacion_chat.py`): Comunicación peer-to-peer con autodescubrimiento

## Ejemplo de Uso

```python
from chat_crdt import ChatCRDT
from sincronizacion_chat import ClienteP2PChat

# Crear chat
chat = ChatCRDT("mi_usuario")

# Enviar mensaje
mensaje_id = chat.enviar_mensaje(
    "¡Hola! Este es mi primer mensaje en el chat CRDT."
)

# Crear canal
chat.crear_canal("tecnologia")

# Enviar mensaje a canal específico
chat.enviar_mensaje(
    "Hablemos de CRDTs aquí",
    canal="tecnologia"
)

# Editar mensaje
chat.editar_mensaje(mensaje_id, "¡Hola! Mensaje editado.")

# Buscar mensajes
resultados = chat.buscar_mensajes("CRDT")

# Configurar cliente P2P con autodescubrimiento
cliente = ClienteP2PChat(chat, "Mi Usuario")
cliente.iniciar()

# Ver nodos descubiertos
nodos = cliente.obtener_nodos_descubiertos()
print(f"Encontrados {len(nodos)} nodos")
```

## Demostraciones Incluidas

### Demo Básico del Chat
- Envío de mensajes con timestamps
- Creación de canales temáticos
- Búsqueda de mensajes por contenido
- Estadísticas de actividad en tiempo real

### Demo de Colaboración Multi-usuario
- Múltiples usuarios chateando simultáneamente
- Sincronización automática de mensajes
- Verificación de convergencia entre todos los nodos

### Demo de Edición de Mensajes
- Edición de mensajes propios
- Eliminación de mensajes (soft delete)
- Historial de cambios preservado

### Demo P2P con Autodescubrimiento
- Descubrimiento automático de nodos cercanos
- Conexión automática entre usuarios
- Lista en vivo de participantes conectados

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