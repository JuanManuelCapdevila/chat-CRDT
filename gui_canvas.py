"""
Interfaz gráfica con Canvas para el crucigrama cooperativo
Versión optimizada usando Canvas en lugar de widgets individuales
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import threading
import time
import math
from crucigrama_crdt import CrucigramaCRDT, Celda
from sincronizacion import ClienteP2P
from generador_crucigramas import GeneradorCrucigramas, DiccionarioPalabras


class CrucigramaCanvas:
    """Canvas optimizado para renderizar el crucigrama"""
    
    def __init__(self, parent, crucigrama: CrucigramaCRDT, callback_cambio):
        self.crucigrama = crucigrama
        self.callback_cambio = callback_cambio
        
        # Configuración visual
        self.tamaño_celda = 30
        self.margen = 20
        self.color_fondo = "#FFFFFF"
        self.color_borde = "#000000"
        self.color_celda_negra = "#000000"
        self.color_celda_seleccionada = "#E3F2FD"
        self.color_celda_resaltada = "#FFF9C4"
        self.color_numero = "#1976D2"
        self.color_autor = "#666666"
        self.color_letra = "#000000"
        
        # Estado de interacción
        self.celda_seleccionada = None
        self.celda_hover = None
        self.entrada_activa = False
        
        # Crear canvas
        self.canvas = tk.Canvas(
            parent, 
            bg=self.color_fondo,
            highlightthickness=0,
            cursor="hand2"
        )
        
        # Calcular dimensiones
        self._calcular_dimensiones()
        
        # Configurar scrollbars
        self._configurar_scrollbars(parent)
        
        # Configurar eventos
        self._configurar_eventos()
        
        # Entry invisible para capturar texto
        self.entry_invisible = tk.Entry(parent, width=1, bd=0, highlightthickness=0)
        self.entry_invisible.place(x=-100, y=-100)  # Fuera de vista
        self.entry_invisible.bind('<KeyPress>', self._on_key_press)
        self.entry_invisible.bind('<FocusOut>', self._on_entry_focus_out)
        
        # Renderizar inicial
        self.actualizar_canvas()
    
    def _calcular_dimensiones(self):
        """Calcula las dimensiones necesarias del canvas"""
        self.ancho_grid = self.crucigrama.columnas * self.tamaño_celda
        self.alto_grid = self.crucigrama.filas * self.tamaño_celda
        self.ancho_total = self.ancho_grid + 2 * self.margen + 60  # Extra para números
        self.alto_total = self.alto_grid + 2 * self.margen + 60   # Extra para números
        
        self.canvas.configure(
            width=min(800, self.ancho_total),
            height=min(600, self.alto_total),
            scrollregion=(0, 0, self.ancho_total, self.alto_total)
        )
    
    def _configurar_scrollbars(self, parent):
        """Configura las scrollbars del canvas"""
        # Scrollbar vertical
        self.v_scrollbar = ttk.Scrollbar(parent, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # Scrollbar horizontal
        self.h_scrollbar = ttk.Scrollbar(parent, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Empaquetado
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Configurar expansión
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Scroll con rueda del mouse
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
    
    def _configurar_eventos(self):
        """Configura los eventos del canvas"""
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.focus_set()  # Para recibir eventos de teclado
    
    def _on_mousewheel(self, event):
        """Maneja el scroll con rueda del mouse"""
        if event.delta:
            delta = -1 * (event.delta / 120)
        else:
            delta = -1 if event.num == 4 else 1
        
        self.canvas.yview_scroll(int(delta), "units")
    
    def _on_click(self, event):
        """Maneja clicks en el canvas"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        fila, columna = self._pixel_a_celda(canvas_x, canvas_y)
        
        if self._es_celda_valida(fila, columna):
            celda = self.crucigrama.obtener_celda(fila, columna)
            
            # No seleccionar celdas negras
            if celda and celda.es_negra:
                return
            
            self.celda_seleccionada = (fila, columna)
            self._activar_entrada_texto()
            self.actualizar_canvas()
    
    def _on_right_click(self, event):
        """Maneja click derecho para celdas negras"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        fila, columna = self._pixel_a_celda(canvas_x, canvas_y)
        
        if self._es_celda_valida(fila, columna):
            celda = self.crucigrama.obtener_celda(fila, columna)
            
            if celda and celda.es_negra:
                # Convertir a celda normal
                self.callback_cambio(fila, columna, None)
            else:
                # Convertir a celda negra
                self.callback_cambio(fila, columna, 'NEGRA')
            
            self.actualizar_canvas()
    
    def _on_motion(self, event):
        """Maneja movimiento del mouse para hover"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        fila, columna = self._pixel_a_celda(canvas_x, canvas_y)
        
        if self._es_celda_valida(fila, columna):
            if self.celda_hover != (fila, columna):
                self.celda_hover = (fila, columna)
                self.actualizar_canvas()
        else:
            if self.celda_hover is not None:
                self.celda_hover = None
                self.actualizar_canvas()
    
    def _on_leave(self, event):
        """Maneja cuando el mouse sale del canvas"""
        if self.celda_hover is not None:
            self.celda_hover = None
            self.actualizar_canvas()
    
    def _pixel_a_celda(self, x, y):
        """Convierte coordenadas de pixel a fila/columna"""
        fila = int((y - self.margen - 30) / self.tamaño_celda)
        columna = int((x - self.margen - 30) / self.tamaño_celda)
        return fila, columna
    
    def _celda_a_pixel(self, fila, columna):
        """Convierte fila/columna a coordenadas de pixel"""
        x = self.margen + 30 + columna * self.tamaño_celda
        y = self.margen + 30 + fila * self.tamaño_celda
        return x, y
    
    def _es_celda_valida(self, fila, columna):
        """Verifica si la celda está dentro del grid"""
        return (0 <= fila < self.crucigrama.filas and 
                0 <= columna < self.crucigrama.columnas)
    
    def _activar_entrada_texto(self):
        """Activa la entrada de texto"""
        if not self.entrada_activa:
            self.entrada_activa = True
            self.entry_invisible.focus_set()
    
    def _on_key_press(self, event):
        """Maneja la entrada de teclas"""
        if not self.celda_seleccionada:
            return
        
        fila, columna = self.celda_seleccionada
        tecla = event.char.upper()
        
        # Solo letras y backspace
        if tecla.isalpha():
            self.callback_cambio(fila, columna, tecla)
            self.actualizar_canvas()
            # Mover a siguiente celda horizontal
            self._mover_seleccion(0, 1)
        elif event.keysym == 'BackSpace':
            self.callback_cambio(fila, columna, None)
            self.actualizar_canvas()
            # Mover a celda anterior
            self._mover_seleccion(0, -1)
        elif event.keysym in ['Up', 'Down', 'Left', 'Right']:
            self._manejar_navegacion(event.keysym)
        elif event.keysym == 'Escape':
            self._desactivar_entrada_texto()
    
    def _manejar_navegacion(self, tecla):
        """Maneja las teclas de navegación"""
        if not self.celda_seleccionada:
            return
        
        fila, columna = self.celda_seleccionada
        
        if tecla == 'Up':
            self._mover_seleccion(-1, 0)
        elif tecla == 'Down':
            self._mover_seleccion(1, 0)
        elif tecla == 'Left':
            self._mover_seleccion(0, -1)
        elif tecla == 'Right':
            self._mover_seleccion(0, 1)
    
    def _mover_seleccion(self, delta_fila, delta_columna):
        """Mueve la selección de celda"""
        if not self.celda_seleccionada:
            return
        
        fila, columna = self.celda_seleccionada
        nueva_fila = max(0, min(self.crucigrama.filas - 1, fila + delta_fila))
        nueva_columna = max(0, min(self.crucigrama.columnas - 1, columna + delta_columna))
        
        # Evitar celdas negras
        celda = self.crucigrama.obtener_celda(nueva_fila, nueva_columna)
        if celda and celda.es_negra:
            return
        
        self.celda_seleccionada = (nueva_fila, nueva_columna)
        self.actualizar_canvas()
        
        # Hacer scroll para mantener visible
        self._scroll_a_celda(nueva_fila, nueva_columna)
    
    def _scroll_a_celda(self, fila, columna):
        """Hace scroll para mantener visible una celda"""
        x, y = self._celda_a_pixel(fila, columna)
        
        # Obtener dimensiones visibles
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calcular si necesita scroll
        scroll_x = self.canvas.canvasx(0)
        scroll_y = self.canvas.canvasy(0)
        
        if x < scroll_x or x > scroll_x + canvas_width:
            self.canvas.xview_moveto((x - canvas_width/2) / self.ancho_total)
        
        if y < scroll_y or y > scroll_y + canvas_height:
            self.canvas.yview_moveto((y - canvas_height/2) / self.alto_total)
    
    def _on_entry_focus_out(self, event):
        """Maneja cuando el entry pierde el foco"""
        self.entrada_activa = False
    
    def _desactivar_entrada_texto(self):
        """Desactiva la entrada de texto"""
        self.entrada_activa = False
        self.celda_seleccionada = None
        self.canvas.focus_set()
        self.actualizar_canvas()
    
    def actualizar_canvas(self):
        """Actualiza completamente el canvas"""
        self.canvas.delete("all")
        
        # Dibujar números de fila y columna
        self._dibujar_numeros_guia()
        
        # Dibujar grid
        self._dibujar_grid()
        
        # Dibujar contenido de celdas
        self._dibujar_contenido_celdas()
    
    def _dibujar_numeros_guia(self):
        """Dibuja los números de fila y columna"""
        # Números de columna
        for col in range(self.crucigrama.columnas):
            x = self.margen + 30 + col * self.tamaño_celda + self.tamaño_celda // 2
            y = self.margen + 15
            
            self.canvas.create_text(
                x, y, text=str(col),
                font=("Arial", 8), fill=self.color_numero
            )
        
        # Números de fila
        for fila in range(self.crucigrama.filas):
            x = self.margen + 15
            y = self.margen + 30 + fila * self.tamaño_celda + self.tamaño_celda // 2
            
            self.canvas.create_text(
                x, y, text=str(fila),
                font=("Arial", 8), fill=self.color_numero
            )
    
    def _dibujar_grid(self):
        """Dibuja el grid del crucigrama"""
        for fila in range(self.crucigrama.filas):
            for columna in range(self.crucigrama.columnas):
                self._dibujar_celda(fila, columna)
    
    def _dibujar_celda(self, fila, columna):
        """Dibuja una celda específica"""
        x, y = self._celda_a_pixel(fila, columna)
        
        celda = self.crucigrama.obtener_celda(fila, columna)
        
        # Determinar color de fondo
        if celda and celda.es_negra:
            color_fondo = self.color_celda_negra
        elif self.celda_seleccionada == (fila, columna):
            color_fondo = self.color_celda_seleccionada
        elif self.celda_hover == (fila, columna):
            color_fondo = self.color_celda_resaltada
        else:
            color_fondo = self.color_fondo
        
        # Dibujar rectángulo de celda
        self.canvas.create_rectangle(
            x, y, x + self.tamaño_celda, y + self.tamaño_celda,
            fill=color_fondo, outline=self.color_borde, width=1
        )
    
    def _dibujar_contenido_celdas(self):
        """Dibuja el contenido de todas las celdas"""
        for fila in range(self.crucigrama.filas):
            for columna in range(self.crucigrama.columnas):
                self._dibujar_contenido_celda(fila, columna)
    
    def _dibujar_contenido_celda(self, fila, columna):
        """Dibuja el contenido de una celda específica"""
        celda = self.crucigrama.obtener_celda(fila, columna)
        if not celda or celda.es_negra:
            return
        
        x, y = self._celda_a_pixel(fila, columna)
        
        # Dibujar número (esquina superior izquierda)
        if celda.numero:
            self.canvas.create_text(
                x + 4, y + 6, text=str(celda.numero),
                font=("Arial", 8, "bold"), fill=self.color_numero,
                anchor='nw'
            )
        
        # Dibujar letra (centro)
        if celda.letra:
            centro_x = x + self.tamaño_celda // 2
            centro_y = y + self.tamaño_celda // 2
            
            self.canvas.create_text(
                centro_x, centro_y, text=celda.letra,
                font=("Arial", 12, "bold"), fill=self.color_letra
            )
        
        # Dibujar autor (esquina inferior derecha)
        if celda.autor:
            autor_texto = celda.autor[:3]  # Solo primeros 3 caracteres
            self.canvas.create_text(
                x + self.tamaño_celda - 2, y + self.tamaño_celda - 2,
                text=autor_texto, font=("Arial", 6), fill=self.color_autor,
                anchor='se'
            )


class CrucigramaCanvasGUI:
    """Interfaz principal usando Canvas"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Crucigrama Cooperativo - Canvas")
        self.root.geometry("1200x800")
        self.root.state('zoomed' if tk.sys.platform == 'win32' else 'normal')
        
        # Datos del usuario
        self.nombre_usuario = self._solicitar_nombre_usuario()
        self.crucigrama = CrucigramaCRDT(15, 15, self.nombre_usuario)
        self.cliente_p2p = ClienteP2P(
            self.crucigrama,
            nombre_usuario=self.nombre_usuario,
            habilitar_autodescubrimiento=True
        )
        
        # Generador
        self.generador = GeneradorCrucigramas()
        
        # Variables de estado
        self.actualizacion_automatica = True
        
        # Configurar interfaz
        self._configurar_interfaz()
        
        # Iniciar servicios
        self._iniciar_servicios()
    
    def _solicitar_nombre_usuario(self):
        """Solicita el nombre del usuario al iniciar"""
        nombre = simpledialog.askstring("Usuario", "Ingresa tu nombre:")
        return nombre if nombre else f"Usuario{time.time():.0f}"
    
    def _configurar_interfaz(self):
        """Configura la interfaz principal"""
        # Configurar grid principal
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Panel superior - información
        self._crear_panel_info()
        
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Frame para canvas (izquierda)
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Crear canvas del crucigrama
        self.crucigrama_canvas = CrucigramaCanvas(
            canvas_frame, self.crucigrama, self._on_celda_cambio
        )
        
        # Panel de controles (derecha)
        self._crear_panel_controles(main_frame)
    
    def _crear_panel_info(self):
        """Crea el panel de información superior"""
        info_frame = tk.Frame(self.root, relief='sunken', bd=2, bg='#f0f0f0')
        info_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 0))
        
        # Información del usuario
        tk.Label(
            info_frame, 
            text=f"Usuario: {self.nombre_usuario}", 
            font=('Arial', 12, 'bold'),
            bg='#f0f0f0'
        ).pack(side='left', padx=10, pady=5)
        
        tk.Label(
            info_frame,
            text=f"Node ID: {self.crucigrama.node_id}",
            font=('Arial', 10),
            bg='#f0f0f0'
        ).pack(side='left', padx=10, pady=5)
        
        # Estado de conexión
        self.conexion_label = tk.Label(
            info_frame, 
            text="Iniciando...", 
            fg='orange', 
            font=('Arial', 10, 'bold'),
            bg='#f0f0f0'
        )
        self.conexion_label.pack(side='right', padx=10, pady=5)
        
        # Botón de ayuda
        tk.Button(
            info_frame,
            text="?",
            font=('Arial', 8, 'bold'),
            command=self._mostrar_ayuda,
            width=3
        ).pack(side='right', padx=5, pady=2)
    
    def _crear_panel_controles(self, parent):
        """Crea el panel de controles lateral"""
        controles_frame = tk.Frame(parent, relief='sunken', bd=2, width=350)
        controles_frame.grid(row=0, column=1, sticky='nsew')
        controles_frame.grid_propagate(False)
        
        # Título
        tk.Label(
            controles_frame, 
            text="Panel de Control", 
            font=('Arial', 14, 'bold')
        ).pack(pady=10)
        
        # Botones principales
        self._crear_botones_principales(controles_frame)
        
        # Generación automática
        self._crear_seccion_generacion(controles_frame)
        
        # Lista de palabras
        self._crear_seccion_palabras(controles_frame)
        
        # Log de actividad
        self._crear_seccion_log(controles_frame)
        
        # Estadísticas
        self._crear_seccion_estadisticas(controles_frame)
    
    def _crear_botones_principales(self, parent):
        """Crea los botones principales de acción"""
        botones_frame = tk.LabelFrame(parent, text="Acciones")
        botones_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(
            botones_frame, 
            text="➕ Agregar Palabra",
            command=self._agregar_palabra_dialog,
            font=('Arial', 10)
        ).pack(fill='x', padx=5, pady=2)
        
        tk.Button(
            botones_frame,
            text="🔍 Buscar Nodos",
            command=self._buscar_nodos,
            font=('Arial', 10)
        ).pack(fill='x', padx=5, pady=2)
        
        tk.Button(
            botones_frame,
            text="📊 Ver Nodos",
            command=self._mostrar_nodos_descubiertos,
            font=('Arial', 10)
        ).pack(fill='x', padx=5, pady=2)
        
        tk.Button(
            botones_frame,
            text="🗑️ Limpiar Todo",
            command=self._limpiar_crucigrama,
            font=('Arial', 10),
            fg='red'
        ).pack(fill='x', padx=5, pady=2)
    
    def _crear_seccion_generacion(self, parent):
        """Crea la sección de generación automática"""
        gen_frame = tk.LabelFrame(parent, text="Generación Automática")
        gen_frame.pack(fill='x', padx=10, pady=5)
        
        # Botones rápidos
        botones_rapidos = [
            ("🚀 Fácil", "facil"),
            ("⚡ Difícil", "dificil"),
            ("💻 Tecnología", "tecnologia"),
            ("🧪 Ciencia", "ciencia")
        ]
        
        for texto, tipo in botones_rapidos:
            tk.Button(
                gen_frame,
                text=texto,
                command=lambda t=tipo: self._generar_crucigrama(t),
                font=('Arial', 9)
            ).pack(fill='x', padx=5, pady=1)
        
        tk.Button(
            gen_frame,
            text="⚙️ Personalizado",
            command=self._generar_personalizado_dialog,
            font=('Arial', 9, 'bold')
        ).pack(fill='x', padx=5, pady=2)
    
    def _crear_seccion_palabras(self, parent):
        """Crea la sección de lista de palabras"""
        palabras_frame = tk.LabelFrame(parent, text="Palabras")
        palabras_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Listbox con scrollbar
        list_frame = tk.Frame(palabras_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.palabras_listbox = tk.Listbox(list_frame, height=6, font=('Arial', 9))
        palabras_scrollbar = ttk.Scrollbar(list_frame, orient='vertical')
        
        self.palabras_listbox.configure(yscrollcommand=palabras_scrollbar.set)
        palabras_scrollbar.configure(command=self.palabras_listbox.yview)
        
        self.palabras_listbox.pack(side='left', fill='both', expand=True)
        palabras_scrollbar.pack(side='right', fill='y')
    
    def _crear_seccion_log(self, parent):
        """Crea la sección de log de actividad"""
        log_frame = tk.LabelFrame(parent, text="Actividad")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=6, 
            width=30,
            font=('Consolas', 8),
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def _crear_seccion_estadisticas(self, parent):
        """Crea la sección de estadísticas"""
        stats_frame = tk.LabelFrame(parent, text="Estadísticas")
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = tk.Label(
            stats_frame,
            text="Cargando...",
            font=('Arial', 9),
            justify='left',
            anchor='w'
        )
        self.stats_label.pack(fill='x', padx=5, pady=5)
    
    def _on_celda_cambio(self, fila, columna, valor):
        """Maneja cambios en las celdas del canvas"""
        if valor == 'NEGRA':
            self.crucigrama.establecer_celda_negra(fila, columna, self.nombre_usuario)
            self._log(f"Celda ({fila},{columna}) marcada como negra")
        elif valor is None:
            self.crucigrama.establecer_letra(fila, columna, None, self.nombre_usuario)
            self._log(f"Celda ({fila},{columna}) limpiada")
        else:
            self.crucigrama.establecer_letra(fila, columna, valor, self.nombre_usuario)
            self._log(f"Letra '{valor}' en ({fila},{columna})")
        
        # Sincronizar cambios
        self.cliente_p2p.enviar_cambio_local()
        self._actualizar_estadisticas()
    
    def _generar_crucigrama(self, tipo: str):
        """Genera crucigrama automáticamente"""
        try:
            if messagebox.askyesno("Confirmar", f"¿Generar crucigrama {tipo}?\nEsto reemplazará el crucigrama actual."):
                self._log(f"Generando crucigrama {tipo}...")
                
                if tipo == "facil":
                    nuevo_crucigrama = self.generador.generar_plantilla_facil()
                elif tipo == "dificil":
                    nuevo_crucigrama = self.generador.generar_plantilla_dificil()
                elif tipo in ["tecnologia", "ciencia", "geografia", "historia"]:
                    nuevo_crucigrama = self.generador.generar_crucigrama_tematico(tipo)
                else:
                    nuevo_crucigrama = self.generador.generar_crucigrama_basico()
                
                self._cargar_crucigrama_generado(nuevo_crucigrama)
                self._log(f"✅ Crucigrama {tipo} generado ({len(nuevo_crucigrama.palabras)} palabras)")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generando crucigrama: {e}")
            self._log(f"❌ Error: {e}")
    
    def _cargar_crucigrama_generado(self, nuevo_crucigrama):
        """Carga crucigrama generado manteniendo configuración"""
        # Limpiar crucigrama actual
        self.crucigrama = CrucigramaCRDT(15, 15, self.nombre_usuario)
        
        # Cargar palabras del nuevo crucigrama
        for numero, palabra in nuevo_crucigrama.palabras.items():
            self.crucigrama.agregar_palabra(
                palabra.pista,
                palabra.respuesta,
                palabra.fila_inicio,
                palabra.columna_inicio,
                palabra.direccion,
                self.nombre_usuario
            )
        
        # Actualizar canvas y GUI
        self.crucigrama_canvas.crucigrama = self.crucigrama
        self.crucigrama_canvas.actualizar_canvas()
        self._actualizar_palabras_lista()
        self.cliente_p2p.enviar_cambio_local()
    
    def _agregar_palabra_dialog(self):
        """Abre diálogo para agregar palabra"""
        from gui_crucigrama import AgregarPalabraDialog  # Import local para evitar circular
        AgregarPalabraDialog(self.root, self._on_palabra_agregada)
    
    def _on_palabra_agregada(self, pista, respuesta, fila, columna, direccion):
        """Callback cuando se agrega una palabra"""
        numero = self.crucigrama.agregar_palabra(
            pista, respuesta, fila, columna, direccion, self.nombre_usuario
        )
        
        if numero:
            self._log(f"✅ Palabra '{respuesta}' agregada (#{numero})")
            self.crucigrama_canvas.actualizar_canvas()
            self._actualizar_palabras_lista()
            self.cliente_p2p.enviar_cambio_local()
        else:
            messagebox.showerror("Error", "No se pudo agregar la palabra")
    
    def _generar_personalizado_dialog(self):
        """Diálogo para crucigrama personalizado"""
        from gui_crucigrama import GenerarPersonalizadoDialog
        GenerarPersonalizadoDialog(self.root, self._on_crucigrama_personalizado)
    
    def _on_crucigrama_personalizado(self, categoria, num_palabras, dificultad):
        """Callback para crucigrama personalizado"""
        try:
            self._log(f"Generando crucigrama personalizado: {categoria}")
            
            if categoria == "mixto":
                crucigrama = self.generador.generar_crucigrama_basico(num_palabras=num_palabras)
            else:
                crucigrama = self.generador.generar_crucigrama_tematico(categoria)
            
            self._cargar_crucigrama_generado(crucigrama)
            self._log(f"✅ Crucigrama personalizado listo")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
    
    def _buscar_nodos(self):
        """Busca nodos en la red"""
        if self.cliente_p2p.autodescubrimiento_habilitado:
            self._log("🔍 Buscando nodos cercanos...")
            nodos = self.cliente_p2p.obtener_nodos_descubiertos()
            if nodos:
                self.conexion_label.config(text=f"Conectado ({len(nodos)})", fg='green')
                for nodo in nodos:
                    self._log(f"📡 {nodo.nombre_usuario} ({nodo.ip_address})")
            else:
                self._log("❌ No se encontraron nodos")
        else:
            self._log("❌ Autodescubrimiento deshabilitado")
    
    def _mostrar_nodos_descubiertos(self):
        """Muestra ventana de nodos descubiertos"""
        from gui_crucigrama import VentanaNodosDescubiertos
        VentanaNodosDescubiertos(self.root, self.cliente_p2p)
    
    def _limpiar_crucigrama(self):
        """Limpia todo el crucigrama"""
        if messagebox.askyesno("Confirmar", "¿Limpiar todo el crucigrama?"):
            self.crucigrama = CrucigramaCRDT(15, 15, self.nombre_usuario)
            self.crucigrama_canvas.crucigrama = self.crucigrama
            self.crucigrama_canvas.actualizar_canvas()
            self._actualizar_palabras_lista()
            self._log("🗑️ Crucigrama limpiado")
    
    def _mostrar_ayuda(self):
        """Muestra ventana de ayuda"""
        ayuda = """
🎯 CRUCIGRAMA COOPERATIVO - AYUDA

🖱️ CONTROLES DEL CANVAS:
• Click izquierdo: Seleccionar celda
• Click derecho: Marcar/desmarcar celda negra  
• Teclear: Escribir letra en celda seleccionada
• Flechas: Navegar entre celdas
• Escape: Deseleccionar celda

⚡ GENERACIÓN AUTOMÁTICA:
• Botones temáticos para crucigramas específicos
• Personalizado para configuración avanzada
• Más de 100 palabras en 6 categorías

🌐 COLABORACIÓN:
• Autodescubrimiento automático de usuarios
• Sincronización en tiempo real
• Resolución automática de conflictos

📝 FUNCIONES:
• Agregar palabras manualmente
• Ver lista de palabras y pistas
• Log de actividad en tiempo real
• Estadísticas del crucigrama
        """
        
        ventana_ayuda = tk.Toplevel(self.root)
        ventana_ayuda.title("Ayuda")
        ventana_ayuda.geometry("500x600")
        ventana_ayuda.resizable(False, False)
        
        text_widget = scrolledtext.ScrolledText(
            ventana_ayuda, 
            wrap='word', 
            font=('Arial', 10),
            padx=20,
            pady=20
        )
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', ayuda)
        text_widget.config(state='disabled')
    
    def _actualizar_palabras_lista(self):
        """Actualiza la lista de palabras"""
        self.palabras_listbox.delete(0, 'end')
        for numero, palabra in sorted(self.crucigrama.palabras.items()):
            direccion = "→" if palabra.direccion == "horizontal" else "↓"
            texto = f"{numero}. {direccion} {palabra.respuesta}"
            self.palabras_listbox.insert('end', texto)
    
    def _actualizar_estadisticas(self):
        """Actualiza estadísticas en tiempo real"""
        num_palabras = len(self.crucigrama.palabras)
        celdas_ocupadas = sum(
            1 for f in range(self.crucigrama.filas)
            for c in range(self.crucigrama.columnas)
            if self.crucigrama.obtener_celda(f, c) and 
               (self.crucigrama.obtener_celda(f, c).letra or 
                self.crucigrama.obtener_celda(f, c).es_negra)
        )
        
        nodos_conectados = len(self.cliente_p2p.obtener_nodos_descubiertos())
        
        stats_texto = f"""📊 Palabras: {num_palabras}
📱 Celdas: {celdas_ocupadas}  
🌐 Nodos: {nodos_conectados}
👤 Usuario: {self.nombre_usuario[:10]}"""
        
        self.stats_label.config(text=stats_texto)
    
    def _log(self, mensaje):
        """Agrega mensaje al log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {mensaje}\n")
        self.log_text.see('end')
    
    def _iniciar_servicios(self):
        """Inicia todos los servicios"""
        # Iniciar autodescubrimiento
        if self.cliente_p2p.autodescubrimiento_habilitado:
            try:
                self.cliente_p2p.iniciar_autodescubrimiento()
                self._log("🚀 Sistema iniciado")
                self.conexion_label.config(text="Buscando...", fg='orange')
            except Exception as e:
                self._log(f"❌ Error iniciando: {e}")
        
        # Iniciar actualización automática
        self._iniciar_actualizacion_automatica()
    
    def _iniciar_actualizacion_automatica(self):
        """Inicia actualización automática de la interfaz"""
        def actualizar():
            while self.actualizacion_automatica:
                try:
                    self.root.after(0, self._actualizar_periodica)
                    time.sleep(2)  # Actualizar cada 2 segundos
                except:
                    break
        
        thread = threading.Thread(target=actualizar, daemon=True)
        thread.start()
    
    def _actualizar_periodica(self):
        """Actualización periódica de la interfaz"""
        # Actualizar canvas
        self.crucigrama_canvas.actualizar_canvas()
        
        # Actualizar listas y estadísticas
        self._actualizar_palabras_lista()
        self._actualizar_estadisticas()
    
    def ejecutar(self):
        """Ejecuta la aplicación"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()
    
    def _on_closing(self):
        """Maneja el cierre de la aplicación"""
        self.actualizacion_automatica = False
        self.cliente_p2p.detener_sync()
        self.root.quit()
        self.root.destroy()


def main():
    """Función principal"""
    try:
        app = CrucigramaCanvasGUI()
        app.ejecutar()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()