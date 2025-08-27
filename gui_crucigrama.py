"""
Interfaz gráfica con tkinter para el crucigrama cooperativo
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import threading
import time
from crucigrama_crdt import CrucigramaCRDT, Celda
from sincronizacion import ClienteP2P
from generador_crucigramas import GeneradorCrucigramas, DiccionarioPalabras


class CeldaWidget:
    """Widget personalizado para representar una celda del crucigrama"""
    
    def __init__(self, parent, fila, columna, callback):
        self.fila = fila
        self.columna = columna
        self.callback = callback
        
        # Frame contenedor
        self.frame = tk.Frame(parent, relief='raised', borderwidth=1, 
                             width=40, height=40)
        self.frame.grid_propagate(False)
        
        # Entry para la letra
        self.entry = tk.Entry(self.frame, width=2, justify='center', 
                             font=('Arial', 14, 'bold'), bd=0, 
                             highlightthickness=0)
        self.entry.pack(expand=True, fill='both')
        
        # Label para el número (esquina superior izquierda)
        self.numero_label = tk.Label(self.frame, text="", font=('Arial', 8),
                                    fg='blue', bg='white')
        self.numero_label.place(x=2, y=2)
        
        # Label para el autor (esquina inferior derecha)
        self.autor_label = tk.Label(self.frame, text="", font=('Arial', 6),
                                   fg='gray', bg='white')
        self.autor_label.place(relx=1, rely=1, anchor='se', x=-2, y=-2)
        
        # Eventos
        self.entry.bind('<KeyRelease>', self._on_key_release)
        self.entry.bind('<Button-3>', self._on_right_click)  # Click derecho
        
        # Estado
        self.es_negra = False
    
    def _on_key_release(self, event):
        """Maneja la escritura de letras"""
        letra = self.entry.get().upper()
        if len(letra) > 1:
            letra = letra[-1]  # Solo la última letra
            self.entry.delete(0, 'end')
            self.entry.insert(0, letra)
        
        self.callback(self.fila, self.columna, letra if letra else None)
    
    def _on_right_click(self, event):
        """Maneja click derecho para marcar como celda negra"""
        if not self.es_negra:
            self.callback(self.fila, self.columna, 'NEGRA')
        else:
            self.callback(self.fila, self.columna, 'NORMAL')
    
    def actualizar_celda(self, celda: Celda):
        """Actualiza la visualización de la celda"""
        if celda.es_negra:
            self.entry.config(state='disabled', bg='black')
            self.numero_label.config(bg='black')
            self.autor_label.config(bg='black')
            self.es_negra = True
        else:
            self.entry.config(state='normal', bg='white')
            self.numero_label.config(bg='white')
            self.autor_label.config(bg='white')
            self.es_negra = False
            
            # Actualizar letra
            self.entry.delete(0, 'end')
            if celda.letra:
                self.entry.insert(0, celda.letra)
            
            # Actualizar número
            if celda.numero:
                self.numero_label.config(text=str(celda.numero))
            else:
                self.numero_label.config(text="")
            
            # Actualizar autor
            if celda.autor:
                self.autor_label.config(text=celda.autor[:3])
            else:
                self.autor_label.config(text="")


class CrucigramaGUI:
    """Interfaz gráfica principal del crucigrama cooperativo"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Crucigrama Cooperativo - CRDT")
        self.root.geometry("900x700")
        
        # Datos del usuario
        self.nombre_usuario = self._solicitar_nombre_usuario()
        self.crucigrama = CrucigramaCRDT(15, 15, self.nombre_usuario)
        self.cliente_p2p = ClienteP2P(
            self.crucigrama, 
            nombre_usuario=self.nombre_usuario,
            habilitar_autodescubrimiento=True
        )
        
        # Widgets del crucigrama
        self.celdas_widgets = {}
        
        # Variables de estado
        self.actualizacion_automatica = True
        self.generador = GeneradorCrucigramas()
        
        # Configurar interfaz
        self._configurar_interfaz()
        
        # Iniciar servicios
        self._iniciar_actualizacion_automatica()
        self._iniciar_autodescubrimiento()
    
    def _solicitar_nombre_usuario(self):
        """Solicita el nombre del usuario al iniciar"""
        nombre = simpledialog.askstring("Usuario", "Ingresa tu nombre:")
        return nombre if nombre else f"Usuario{time.time():.0f}"
    
    def _configurar_interfaz(self):
        """Configura todos los elementos de la interfaz"""
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Panel superior con información
        self._crear_panel_info(main_frame)
        
        # Frame para el crucigrama y controles
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # Panel izquierdo - Crucigrama
        self._crear_panel_crucigrama(content_frame)
        
        # Panel derecho - Controles
        self._crear_panel_controles(content_frame)
    
    def _crear_panel_info(self, parent):
        """Crea el panel de información superior"""
        info_frame = tk.Frame(parent, relief='sunken', bd=2)
        info_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(info_frame, text=f"Usuario: {self.nombre_usuario}", 
                font=('Arial', 12, 'bold')).pack(side='left', padx=10, pady=5)
        
        tk.Label(info_frame, text=f"Node ID: {self.crucigrama.node_id}", 
                font=('Arial', 10)).pack(side='left', padx=10, pady=5)
        
        # Estado de conexión
        self.conexion_label = tk.Label(info_frame, text="Desconectado", 
                                      fg='red', font=('Arial', 10, 'bold'))
        self.conexion_label.pack(side='right', padx=10, pady=5)
    
    def _crear_panel_crucigrama(self, parent):
        """Crea el panel del crucigrama"""
        crucigrama_frame = tk.Frame(parent)
        crucigrama_frame.pack(side='left', fill='both', expand=True)
        
        # Canvas con scrollbars para el crucigrama grande
        canvas = tk.Canvas(crucigrama_frame, bg='white')
        v_scrollbar = ttk.Scrollbar(crucigrama_frame, orient='vertical', command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(crucigrama_frame, orient='horizontal', command=canvas.xview)
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Frame interno para el grid
        self.grid_frame = tk.Frame(canvas, bg='white')
        canvas.create_window((0, 0), window=self.grid_frame, anchor='nw')
        
        # Crear el grid de celdas
        self._crear_grid_celdas()
        
        # Empaquetar canvas y scrollbars
        canvas.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Actualizar scroll region cuando cambie el tamaño
        self.grid_frame.bind('<Configure>', 
                            lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    
    def _crear_grid_celdas(self):
        """Crea el grid de celdas del crucigrama"""
        # Etiquetas de columnas
        for col in range(self.crucigrama.columnas):
            label = tk.Label(self.grid_frame, text=str(col), font=('Arial', 8))
            label.grid(row=0, column=col+1, padx=1, pady=1)
        
        # Crear celdas
        for fila in range(self.crucigrama.filas):
            # Etiqueta de fila
            label = tk.Label(self.grid_frame, text=str(fila), font=('Arial', 8))
            label.grid(row=fila+1, column=0, padx=1, pady=1)
            
            for columna in range(self.crucigrama.columnas):
                celda_widget = CeldaWidget(self.grid_frame, fila, columna, 
                                         self._on_celda_cambio)
                celda_widget.frame.grid(row=fila+1, column=columna+1, 
                                      padx=1, pady=1)
                self.celdas_widgets[(fila, columna)] = celda_widget
    
    def _crear_panel_controles(self, parent):
        """Crea el panel de controles derecho"""
        controles_frame = tk.Frame(parent, relief='sunken', bd=2, width=300)
        controles_frame.pack(side='right', fill='y', padx=(10, 0))
        controles_frame.pack_propagate(False)
        
        # Título
        tk.Label(controles_frame, text="Controles", 
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Botones de acción
        tk.Button(controles_frame, text="Agregar Palabra", 
                 command=self._agregar_palabra_dialog).pack(fill='x', padx=10, pady=5)
        
        # Menú de generación automática
        gen_frame = tk.LabelFrame(controles_frame, text="Generación Automática")
        gen_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(gen_frame, text="Crucigrama Fácil", 
                 command=lambda: self._generar_crucigrama("facil")).pack(fill='x', padx=5, pady=2)
        
        tk.Button(gen_frame, text="Crucigrama Difícil", 
                 command=lambda: self._generar_crucigrama("dificil")).pack(fill='x', padx=5, pady=2)
        
        tk.Button(gen_frame, text="Tecnología", 
                 command=lambda: self._generar_crucigrama("tecnologia")).pack(fill='x', padx=5, pady=2)
        
        tk.Button(gen_frame, text="Ciencia", 
                 command=lambda: self._generar_crucigrama("ciencia")).pack(fill='x', padx=5, pady=2)
        
        tk.Button(gen_frame, text="Personalizado", 
                 command=self._generar_personalizado_dialog).pack(fill='x', padx=5, pady=2)
        
        tk.Button(controles_frame, text="Buscar Nodos", 
                 command=self._buscar_nodos).pack(fill='x', padx=10, pady=5)
        
        tk.Button(controles_frame, text="Ver Nodos Cercanos", 
                 command=self._mostrar_nodos_descubiertos).pack(fill='x', padx=10, pady=5)
        
        tk.Button(controles_frame, text="Limpiar Todo", 
                 command=self._limpiar_crucigrama).pack(fill='x', padx=10, pady=5)
        
        # Lista de palabras
        tk.Label(controles_frame, text="Palabras:", 
                font=('Arial', 12, 'bold')).pack(pady=(20, 5))
        
        self.palabras_listbox = tk.Listbox(controles_frame, height=8)
        self.palabras_listbox.pack(fill='x', padx=10, pady=5)
        
        # Log de actividad
        tk.Label(controles_frame, text="Actividad:", 
                font=('Arial', 12, 'bold')).pack(pady=(20, 5))
        
        self.log_text = scrolledtext.ScrolledText(controles_frame, height=8, width=30)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Panel de estadísticas
        stats_frame = tk.Frame(controles_frame)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_label = tk.Label(stats_frame, text="Estadísticas:\nPalabras: 0\nCeldas: 0", 
                                   font=('Arial', 10), justify='left')
        self.stats_label.pack()
    
    def _on_celda_cambio(self, fila, columna, valor):
        """Maneja los cambios en las celdas"""
        if valor == 'NEGRA':
            self.crucigrama.establecer_celda_negra(fila, columna, self.nombre_usuario)
            self._log(f"Celda ({fila},{columna}) marcada como negra")
        elif valor == 'NORMAL':
            self.crucigrama.establecer_letra(fila, columna, None, self.nombre_usuario)
            self._log(f"Celda ({fila},{columna}) limpiada")
        else:
            self.crucigrama.establecer_letra(fila, columna, valor, self.nombre_usuario)
            if valor:
                self._log(f"Letra '{valor}' en ({fila},{columna})")
        
        # Sincronizar cambios
        self.cliente_p2p.enviar_cambio_local()
        self._actualizar_estadisticas()
    
    def _agregar_palabra_dialog(self):
        """Diálogo para agregar una nueva palabra"""
        dialog = AgregarPalabraDialog(self.root, self._on_palabra_agregada)
    
    def _on_palabra_agregada(self, pista, respuesta, fila, columna, direccion):
        """Callback cuando se agrega una palabra"""
        numero = self.crucigrama.agregar_palabra(
            pista, respuesta, fila, columna, direccion, self.nombre_usuario
        )
        
        if numero:
            self._log(f"Palabra '{respuesta}' agregada (#{numero})")
            self._actualizar_palabras_lista()
            self.cliente_p2p.enviar_cambio_local()
        else:
            messagebox.showerror("Error", "No se pudo agregar la palabra")
    
    def _buscar_nodos(self):
        """Inicia búsqueda activa de nodos"""
        if self.cliente_p2p.autodescubrimiento_habilitado:
            self._log("Iniciando búsqueda de nodos cercanos...")
            # El autodescubrimiento ya está corriendo, solo informamos al usuario
            nodos = self.cliente_p2p.obtener_nodos_descubiertos()
            if nodos:
                self._log(f"Encontrados {len(nodos)} nodos")
                for nodo in nodos:
                    self._log(f"- {nodo.nombre_usuario} ({nodo.ip_address})")
            else:
                self._log("No se encontraron nodos cercanos")
        else:
            self._log("Autodescubrimiento no habilitado")
    
    def _generar_crucigrama(self, tipo: str):
        """Genera un crucigrama automáticamente según el tipo"""
        try:
            if messagebox.askyesno("Confirmar", f"¿Generar crucigrama {tipo}? Esto reemplazará el crucigrama actual."):
                self._log(f"Generando crucigrama {tipo}...")
                
                if tipo == "facil":
                    nuevo_crucigrama = self.generador.generar_plantilla_facil()
                elif tipo == "dificil":
                    nuevo_crucigrama = self.generador.generar_plantilla_dificil()
                elif tipo in ["tecnologia", "ciencia", "geografia", "historia", "general", "deportes"]:
                    nuevo_crucigrama = self.generador.generar_crucigrama_tematico(tipo)
                else:
                    nuevo_crucigrama = self.generador.generar_crucigrama_basico()
                
                # Reemplazar crucigrama actual
                self._cargar_crucigrama_generado(nuevo_crucigrama)
                self._log(f"Crucigrama {tipo} generado con {len(nuevo_crucigrama.palabras)} palabras")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generando crucigrama: {e}")
            self._log(f"Error: {e}")
    
    def _generar_personalizado_dialog(self):
        """Diálogo para generar crucigrama personalizado"""
        GenerarPersonalizadoDialog(self.root, self._on_crucigrama_personalizado_generado)
    
    def _on_crucigrama_personalizado_generado(self, categoria, num_palabras, dificultad):
        """Callback cuando se genera crucigrama personalizado"""
        try:
            self._log(f"Generando crucigrama personalizado: {categoria}, {num_palabras} palabras...")
            
            if categoria == "mixto":
                nuevo_crucigrama = self.generador.generar_crucigrama_basico(
                    num_palabras=num_palabras
                )
            else:
                nuevo_crucigrama = self.generador.generar_crucigrama_tematico(categoria)
            
            self._cargar_crucigrama_generado(nuevo_crucigrama)
            self._log(f"Crucigrama personalizado generado")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
    
    def _cargar_crucigrama_generado(self, nuevo_crucigrama: CrucigramaCRDT):
        """Carga un crucigrama generado automáticamente"""
        # Mantener la configuración del usuario actual
        nombre_usuario = self.nombre_usuario
        node_id = self.crucigrama.node_id
        
        # Actualizar crucigrama manteniendo la identidad del usuario
        nuevo_crucigrama.node_id = node_id
        
        # Transferir palabras al crucigrama actual
        for numero, palabra in nuevo_crucigrama.palabras.items():
            self.crucigrama.agregar_palabra(
                palabra.pista,
                palabra.respuesta,
                palabra.fila_inicio,
                palabra.columna_inicio,
                palabra.direccion,
                nombre_usuario  # Usar nuestro nombre de usuario
            )
        
        # Actualizar vista
        self._actualizar_vista_completa()
        
        # Sincronizar con otros nodos
        self.cliente_p2p.enviar_cambio_local()
    
    def _mostrar_nodos_descubiertos(self):
        """Muestra ventana con nodos descubiertos"""
        VentanaNodosDescubiertos(self.root, self.cliente_p2p)
    
    def _limpiar_crucigrama(self):
        """Limpia todo el crucigrama"""
        if messagebox.askyesno("Confirmar", "¿Limpiar todo el crucigrama?"):
            # Crear nuevo crucigrama
            self.crucigrama = CrucigramaCRDT(15, 15, self.nombre_usuario)
            self.cliente_p2p = ClienteP2P(self.crucigrama)
            self._actualizar_vista_completa()
            self._log("Crucigrama limpiado")
    
    def _actualizar_vista_completa(self):
        """Actualiza toda la vista del crucigrama"""
        for fila in range(self.crucigrama.filas):
            for columna in range(self.crucigrama.columnas):
                celda = self.crucigrama.obtener_celda(fila, columna)
                if celda:
                    self.celdas_widgets[(fila, columna)].actualizar_celda(celda)
        
        self._actualizar_palabras_lista()
        self._actualizar_estadisticas()
    
    def _actualizar_palabras_lista(self):
        """Actualiza la lista de palabras"""
        self.palabras_listbox.delete(0, 'end')
        for numero, palabra in sorted(self.crucigrama.palabras.items()):
            direccion = palabra.direccion[0].upper()
            texto = f"{numero}. {direccion}: {palabra.respuesta}"
            self.palabras_listbox.insert('end', texto)
    
    def _actualizar_estadisticas(self):
        """Actualiza las estadísticas"""
        num_palabras = len(self.crucigrama.palabras)
        celdas_ocupadas = sum(1 for f in range(self.crucigrama.filas) 
                             for c in range(self.crucigrama.columnas)
                             if self.crucigrama.obtener_celda(f, c) and 
                             (self.crucigrama.obtener_celda(f, c).letra or 
                              self.crucigrama.obtener_celda(f, c).es_negra))
        
        self.stats_label.config(text=f"Estadísticas:\nPalabras: {num_palabras}\nCeldas: {celdas_ocupadas}")
    
    def _log(self, mensaje):
        """Agrega mensaje al log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {mensaje}\n")
        self.log_text.see('end')
    
    def _iniciar_actualizacion_automatica(self):
        """Inicia el hilo de actualización automática"""
        def actualizar():
            while self.actualizacion_automatica:
                try:
                    self.root.after(0, self._actualizar_vista_completa)
                    time.sleep(1)  # Actualizar cada segundo
                except:
                    break
        
        thread = threading.Thread(target=actualizar, daemon=True)
        thread.start()
    
    def ejecutar(self):
        """Ejecuta la aplicación"""
        self._log(f"Crucigrama iniciado - Usuario: {self.nombre_usuario}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()
    
    def _iniciar_autodescubrimiento(self):
        """Inicia el sistema de autodescubrimiento"""
        if self.cliente_p2p.autodescubrimiento_habilitado:
            try:
                self.cliente_p2p.iniciar_autodescubrimiento()
                self._log("Sistema de autodescubrimiento iniciado")
                self.conexion_label.config(text="Buscando nodos...", fg='orange')
            except Exception as e:
                self._log(f"Error iniciando autodescubrimiento: {e}")
    
    def _on_closing(self):
        """Maneja el cierre de la aplicación"""
        self.actualizacion_automatica = False
        self.cliente_p2p.detener_sync()
        self.root.quit()
        self.root.destroy()


class AgregarPalabraDialog:
    """Diálogo para agregar una nueva palabra"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Agregar Palabra")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Modal
        
        self._crear_widgets()
    
    def _crear_widgets(self):
        """Crea los widgets del diálogo"""
        # Pista
        tk.Label(self.dialog, text="Pista:", font=('Arial', 12)).pack(pady=10)
        self.pista_entry = tk.Entry(self.dialog, width=40, font=('Arial', 11))
        self.pista_entry.pack(pady=5)
        
        # Respuesta
        tk.Label(self.dialog, text="Respuesta:", font=('Arial', 12)).pack(pady=10)
        self.respuesta_entry = tk.Entry(self.dialog, width=40, font=('Arial', 11))
        self.respuesta_entry.pack(pady=5)
        
        # Posición
        pos_frame = tk.Frame(self.dialog)
        pos_frame.pack(pady=10)
        
        tk.Label(pos_frame, text="Fila:").pack(side='left', padx=5)
        self.fila_entry = tk.Entry(pos_frame, width=5)
        self.fila_entry.pack(side='left', padx=5)
        
        tk.Label(pos_frame, text="Columna:").pack(side='left', padx=5)
        self.columna_entry = tk.Entry(pos_frame, width=5)
        self.columna_entry.pack(side='left', padx=5)
        
        # Dirección
        tk.Label(self.dialog, text="Dirección:", font=('Arial', 12)).pack(pady=10)
        self.direccion_var = tk.StringVar(value="horizontal")
        
        dir_frame = tk.Frame(self.dialog)
        dir_frame.pack(pady=5)
        
        tk.Radiobutton(dir_frame, text="Horizontal", variable=self.direccion_var, 
                      value="horizontal").pack(side='left', padx=10)
        tk.Radiobutton(dir_frame, text="Vertical", variable=self.direccion_var, 
                      value="vertical").pack(side='left', padx=10)
        
        # Botones
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Agregar", command=self._agregar).pack(side='left', padx=10)
        tk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(side='left', padx=10)
    
    def _agregar(self):
        """Agrega la palabra"""
        try:
            pista = self.pista_entry.get().strip()
            respuesta = self.respuesta_entry.get().strip()
            fila = int(self.fila_entry.get())
            columna = int(self.columna_entry.get())
            direccion = self.direccion_var.get()
            
            if not pista or not respuesta:
                messagebox.showerror("Error", "Pista y respuesta son obligatorias")
                return
            
            self.callback(pista, respuesta, fila, columna, direccion)
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Posición debe ser un número válido")


class VentanaNodosDescubiertos:
    """Ventana para mostrar nodos descubiertos y estadísticas"""
    
    def __init__(self, parent, cliente_p2p):
        self.cliente_p2p = cliente_p2p
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Nodos Descubiertos")
        self.ventana.geometry("600x400")
        self.ventana.resizable(True, True)
        
        self._crear_interfaz()
        self._actualizar_datos()
        
        # Actualizar cada 3 segundos
        self._actualizar_periodicamente()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la ventana"""
        # Frame principal
        main_frame = tk.Frame(self.ventana)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        tk.Label(main_frame, text="Nodos Descubiertos en la Red", 
                font=('Arial', 16, 'bold')).pack(pady=(0, 10))
        
        # Frame de estadísticas
        stats_frame = tk.LabelFrame(main_frame, text="Estadísticas", font=('Arial', 12, 'bold'))
        stats_frame.pack(fill='x', pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=4, wrap='word')
        self.stats_text.pack(fill='x', padx=10, pady=10)
        
        # Frame de nodos
        nodos_frame = tk.LabelFrame(main_frame, text="Nodos Activos", font=('Arial', 12, 'bold'))
        nodos_frame.pack(fill='both', expand=True)
        
        # Treeview para mostrar nodos
        columns = ('Nombre', 'Node ID', 'IP', 'Puerto', 'Último Visto')
        self.tree = ttk.Treeview(nodos_frame, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        # Scrollbar para el treeview
        scrollbar = ttk.Scrollbar(nodos_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar treeview y scrollbar
        self.tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        # Botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(button_frame, text="Actualizar", command=self._actualizar_datos).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cerrar", command=self.ventana.destroy).pack(side='right', padx=5)
    
    def _actualizar_datos(self):
        """Actualiza los datos mostrados"""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener nodos descubiertos
        nodos = self.cliente_p2p.obtener_nodos_descubiertos()
        
        # Agregar nodos al treeview
        for nodo in nodos:
            import datetime
            ultimo_visto = datetime.datetime.fromtimestamp(nodo.timestamp).strftime("%H:%M:%S")
            
            self.tree.insert('', 'end', values=(
                nodo.nombre_usuario,
                nodo.node_id[:8] + '...',  # Mostrar solo parte del ID
                nodo.ip_address,
                nodo.puerto,
                ultimo_visto
            ))
        
        # Actualizar estadísticas
        stats = self.cliente_p2p.obtener_estadisticas_descubrimiento()
        stats_texto = f"""Nodos totales: {stats.get('nodos_totales', 0)}
Descubridores activos: {stats.get('descubridores_activos', 0)}
Algoritmos utilizados: {', '.join(stats.get('nodos_por_descubridor', {}).keys())}
Estado: {'Funcionando' if self.cliente_p2p.autodescubrimiento_habilitado else 'Deshabilitado'}"""
        
        self.stats_text.delete(1.0, 'end')
        self.stats_text.insert(1.0, stats_texto)
    
    def _actualizar_periodicamente(self):
        """Actualiza los datos periódicamente"""
        if self.ventana.winfo_exists():
            self._actualizar_datos()
            self.ventana.after(3000, self._actualizar_periodicamente)  # 3 segundos


class GenerarPersonalizadoDialog:
    """Diálogo para generar crucigrama personalizado"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Generar Crucigrama Personalizado")
        self.dialog.geometry("400x350")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Modal
        
        self._crear_widgets()
    
    def _crear_widgets(self):
        """Crea los widgets del diálogo"""
        # Categoría
        tk.Label(self.dialog, text="Categoría:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        self.categoria_var = tk.StringVar(value="mixto")
        categorias = [
            ("Mixto (todas las categorías)", "mixto"),
            ("Tecnología", "tecnologia"),
            ("Ciencia", "ciencia"),
            ("Geografía", "geografia"),
            ("Historia", "historia"),
            ("Cultura General", "general"),
            ("Deportes", "deportes")
        ]
        
        for texto, valor in categorias:
            tk.Radiobutton(self.dialog, text=texto, variable=self.categoria_var, 
                          value=valor, font=('Arial', 10)).pack(anchor='w', padx=20)
        
        # Número de palabras
        tk.Label(self.dialog, text="Número de palabras:", font=('Arial', 12, 'bold')).pack(pady=(20, 5))
        
        self.num_palabras_var = tk.IntVar(value=8)
        palabras_frame = tk.Frame(self.dialog)
        palabras_frame.pack(pady=5)
        
        tk.Scale(palabras_frame, from_=3, to=15, orient='horizontal', 
                variable=self.num_palabras_var, length=200).pack()
        
        # Dificultad
        tk.Label(self.dialog, text="Dificultad:", font=('Arial', 12, 'bold')).pack(pady=(20, 5))
        
        self.dificultad_var = tk.StringVar(value="medio")
        dif_frame = tk.Frame(self.dialog)
        dif_frame.pack(pady=5)
        
        for texto, valor in [("Fácil", "facil"), ("Medio", "medio"), ("Difícil", "dificil")]:
            tk.Radiobutton(dif_frame, text=texto, variable=self.dificultad_var, 
                          value=valor).pack(side='left', padx=10)
        
        # Botones
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Generar", command=self._generar,
                 bg='green', fg='white', font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        tk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(side='left', padx=10)
    
    def _generar(self):
        """Genera el crucigrama personalizado"""
        categoria = self.categoria_var.get()
        num_palabras = self.num_palabras_var.get()
        dificultad = self.dificultad_var.get()
        
        self.callback(categoria, num_palabras, dificultad)
        self.dialog.destroy()