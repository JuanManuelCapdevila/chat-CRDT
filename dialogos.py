"""
Diálogos independientes para el crucigrama cooperativo
Módulo separado para evitar dependencias circulares
"""

import tkinter as tk
from tkinter import ttk, messagebox


class AgregarPalabraDialog:
    """Diálogo para agregar una nueva palabra"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Agregar Palabra")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Modal
        self.dialog.transient(parent)
        
        # Centrar en pantalla
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self._crear_widgets()
        
        # Foco inicial en pista
        self.pista_entry.focus_set()
    
    def _crear_widgets(self):
        """Crea los widgets del diálogo"""
        # Frame principal
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Pista
        tk.Label(main_frame, text="Pista:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 5))
        self.pista_entry = tk.Entry(main_frame, width=50, font=('Arial', 11))
        self.pista_entry.pack(fill='x', pady=(0, 15))
        
        # Respuesta
        tk.Label(main_frame, text="Respuesta:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 5))
        self.respuesta_entry = tk.Entry(main_frame, width=50, font=('Arial', 11))
        self.respuesta_entry.pack(fill='x', pady=(0, 15))
        
        # Posición
        pos_frame = tk.Frame(main_frame)
        pos_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(pos_frame, text="Posición:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 5))
        
        pos_inputs = tk.Frame(pos_frame)
        pos_inputs.pack(fill='x')
        
        tk.Label(pos_inputs, text="Fila:", font=('Arial', 10)).pack(side='left')
        self.fila_entry = tk.Entry(pos_inputs, width=5, font=('Arial', 10))
        self.fila_entry.pack(side='left', padx=(5, 15))
        
        tk.Label(pos_inputs, text="Columna:", font=('Arial', 10)).pack(side='left')
        self.columna_entry = tk.Entry(pos_inputs, width=5, font=('Arial', 10))
        self.columna_entry.pack(side='left', padx=(5, 0))
        
        # Dirección
        tk.Label(main_frame, text="Dirección:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))
        
        self.direccion_var = tk.StringVar(value="horizontal")
        
        dir_frame = tk.Frame(main_frame)
        dir_frame.pack(fill='x', pady=(0, 20))
        
        tk.Radiobutton(
            dir_frame, text="→ Horizontal", variable=self.direccion_var, 
            value="horizontal", font=('Arial', 10)
        ).pack(side='left', padx=(0, 20))
        
        tk.Radiobutton(
            dir_frame, text="↓ Vertical", variable=self.direccion_var, 
            value="vertical", font=('Arial', 10)
        ).pack(side='left')
        
        # Botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        tk.Button(
            button_frame, text="Agregar", command=self._agregar,
            bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'),
            padx=20
        ).pack(side='right', padx=(10, 0))
        
        tk.Button(
            button_frame, text="Cancelar", command=self.dialog.destroy,
            font=('Arial', 12), padx=20
        ).pack(side='right')
        
        # Bindings para Enter
        self.pista_entry.bind('<Return>', lambda e: self.respuesta_entry.focus_set())
        self.respuesta_entry.bind('<Return>', lambda e: self.fila_entry.focus_set())
        self.fila_entry.bind('<Return>', lambda e: self.columna_entry.focus_set())
        self.columna_entry.bind('<Return>', lambda e: self._agregar())
        
        # Binding para Escape
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
    
    def _agregar(self):
        """Agrega la palabra"""
        try:
            pista = self.pista_entry.get().strip()
            respuesta = self.respuesta_entry.get().strip()
            fila = int(self.fila_entry.get())
            columna = int(self.columna_entry.get())
            direccion = self.direccion_var.get()
            
            if not pista:
                messagebox.showerror("Error", "La pista es obligatoria")
                self.pista_entry.focus_set()
                return
                
            if not respuesta:
                messagebox.showerror("Error", "La respuesta es obligatoria")
                self.respuesta_entry.focus_set()
                return
            
            self.callback(pista, respuesta, fila, columna, direccion)
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "La posición debe ser un número válido")


class GenerarPersonalizadoDialog:
    """Diálogo para generar crucigrama personalizado"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Generar Crucigrama Personalizado")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Modal
        self.dialog.transient(parent)
        
        # Centrar en pantalla
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self._crear_widgets()
    
    def _crear_widgets(self):
        """Crea los widgets del diálogo"""
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Título
        titulo = tk.Label(
            main_frame, 
            text="🎯 Configuración del Crucigrama",
            font=('Arial', 16, 'bold'),
            fg='#1976D2'
        )
        titulo.pack(pady=(0, 20))
        
        # Categoría
        cat_frame = tk.LabelFrame(main_frame, text="Categoría", font=('Arial', 12, 'bold'), padx=10, pady=10)
        cat_frame.pack(fill='x', pady=(0, 15))
        
        self.categoria_var = tk.StringVar(value="mixto")
        categorias = [
            ("🌐 Mixto (todas las categorías)", "mixto"),
            ("💻 Tecnología", "tecnologia"),
            ("🧪 Ciencia", "ciencia"),
            ("🌍 Geografía", "geografia"),
            ("📚 Historia", "historia"),
            ("🎨 Cultura General", "general"),
            ("⚽ Deportes", "deportes")
        ]
        
        for texto, valor in categorias:
            tk.Radiobutton(
                cat_frame, text=texto, variable=self.categoria_var, 
                value=valor, font=('Arial', 10), anchor='w'
            ).pack(fill='x', pady=2)
        
        # Número de palabras
        palabras_frame = tk.LabelFrame(main_frame, text="Número de palabras", font=('Arial', 12, 'bold'), padx=10, pady=10)
        palabras_frame.pack(fill='x', pady=(0, 15))
        
        self.num_palabras_var = tk.IntVar(value=8)
        
        # Frame para scale y label
        scale_frame = tk.Frame(palabras_frame)
        scale_frame.pack(fill='x')
        
        self.palabras_scale = tk.Scale(
            scale_frame, from_=3, to=15, orient='horizontal', 
            variable=self.num_palabras_var, length=300,
            command=self._actualizar_label_palabras
        )
        self.palabras_scale.pack(fill='x')
        
        self.palabras_label = tk.Label(scale_frame, text="8 palabras", font=('Arial', 10, 'bold'), fg='#4CAF50')
        self.palabras_label.pack(pady=(5, 0))
        
        # Dificultad
        dif_frame = tk.LabelFrame(main_frame, text="Dificultad", font=('Arial', 12, 'bold'), padx=10, pady=10)
        dif_frame.pack(fill='x', pady=(0, 20))
        
        self.dificultad_var = tk.StringVar(value="medio")
        
        dificultades = [
            ("🟢 Fácil", "facil"),
            ("🟡 Medio", "medio"), 
            ("🔴 Difícil", "dificil")
        ]
        
        dif_buttons = tk.Frame(dif_frame)
        dif_buttons.pack()
        
        for texto, valor in dificultades:
            tk.Radiobutton(
                dif_buttons, text=texto, variable=self.dificultad_var, 
                value=valor, font=('Arial', 11)
            ).pack(side='left', padx=15)
        
        # Botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(
            button_frame, text="🚀 Generar", command=self._generar,
            bg='#4CAF50', fg='white', font=('Arial', 14, 'bold'),
            padx=30, pady=10
        ).pack(side='right', padx=(15, 0))
        
        tk.Button(
            button_frame, text="❌ Cancelar", command=self.dialog.destroy,
            font=('Arial', 12), padx=20, pady=10
        ).pack(side='right')
        
        # Binding para Escape
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Binding para Enter
        self.dialog.bind('<Return>', lambda e: self._generar())
    
    def _actualizar_label_palabras(self, valor):
        """Actualiza el label del número de palabras"""
        num = int(float(valor))
        if num <= 5:
            color = '#4CAF50'  # Verde
            desc = " (rápido)"
        elif num <= 10:
            color = '#FF9800'  # Naranja  
            desc = " (balanceado)"
        else:
            color = '#F44336'  # Rojo
            desc = " (complejo)"
        
        self.palabras_label.config(text=f"{num} palabras{desc}", fg=color)
    
    def _generar(self):
        """Genera el crucigrama personalizado"""
        categoria = self.categoria_var.get()
        num_palabras = self.num_palabras_var.get()
        dificultad = self.dificultad_var.get()
        
        self.callback(categoria, num_palabras, dificultad)
        self.dialog.destroy()


class VentanaNodosDescubiertos:
    """Ventana para mostrar nodos descubiertos y estadísticas"""
    
    def __init__(self, parent, cliente_p2p):
        self.cliente_p2p = cliente_p2p
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("🌐 Nodos Descubiertos")
        self.ventana.geometry("700x500")
        self.ventana.resizable(True, True)
        self.ventana.transient(parent)
        
        self._crear_interfaz()
        self._actualizar_datos()
        
        # Actualizar cada 3 segundos
        self._actualizar_periodicamente()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la ventana"""
        # Frame principal
        main_frame = tk.Frame(self.ventana, padx=15, pady=15)
        main_frame.pack(fill='both', expand=True)
        
        # Título con emoji
        titulo = tk.Label(
            main_frame, 
            text="🌐 Nodos Descubiertos en la Red", 
            font=('Arial', 16, 'bold'),
            fg='#1976D2'
        )
        titulo.pack(pady=(0, 15))
        
        # Frame de estadísticas mejorado
        stats_frame = tk.LabelFrame(
            main_frame, 
            text="📊 Estadísticas de Red", 
            font=('Arial', 12, 'bold'),
            padx=10, pady=10
        )
        stats_frame.pack(fill='x', pady=(0, 15))
        
        self.stats_text = tk.Text(
            stats_frame, 
            height=4, 
            wrap='word',
            font=('Consolas', 10),
            bg='#f8f9fa',
            relief='flat'
        )
        self.stats_text.pack(fill='x', padx=5, pady=5)
        
        # Frame de nodos con mejor estilo
        nodos_frame = tk.LabelFrame(
            main_frame, 
            text="🔗 Nodos Activos", 
            font=('Arial', 12, 'bold'),
            padx=10, pady=10
        )
        nodos_frame.pack(fill='both', expand=True)
        
        # Treeview mejorado
        columns = ('👤 Usuario', '🆔 Node ID', '📡 IP', '🔌 Puerto', '⏰ Último Visto')
        self.tree = ttk.Treeview(nodos_frame, columns=columns, show='headings', height=12)
        
        # Configurar columnas con mejor ancho
        column_widths = [120, 100, 120, 80, 100]
        for i, (col, width) in enumerate(zip(columns, column_widths)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=50)
        
        # Scrollbar para el treeview
        scrollbar = ttk.Scrollbar(nodos_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Frame para tree y scrollbar
        tree_frame = tk.Frame(nodos_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botones mejorados
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(15, 0))
        
        tk.Button(
            button_frame, text="🔄 Actualizar", command=self._actualizar_datos,
            font=('Arial', 10, 'bold'), bg='#2196F3', fg='white', padx=20
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            button_frame, text="❌ Cerrar", command=self.ventana.destroy,
            font=('Arial', 10), padx=20
        ).pack(side='right')
        
        # Binding para Escape
        self.ventana.bind('<Escape>', lambda e: self.ventana.destroy())
    
    def _actualizar_datos(self):
        """Actualiza los datos mostrados"""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener nodos descubiertos
        nodos = self.cliente_p2p.obtener_nodos_descubiertos()
        
        # Agregar nodos al treeview con colores alternos
        for i, nodo in enumerate(nodos):
            import datetime
            ultimo_visto = datetime.datetime.fromtimestamp(nodo.timestamp).strftime("%H:%M:%S")
            
            # Determinar color basado en qué tan reciente es
            tiempo_actual = datetime.datetime.now().timestamp()
            diferencia = tiempo_actual - nodo.timestamp
            
            if diferencia < 10:  # Muy reciente
                tag = 'reciente'
            elif diferencia < 30:  # Reciente
                tag = 'medio'
            else:  # Viejo
                tag = 'viejo'
            
            self.tree.insert('', 'end', values=(
                nodo.nombre_usuario,
                nodo.node_id[:8] + '...',  # Mostrar solo parte del ID
                nodo.ip_address,
                nodo.puerto,
                ultimo_visto
            ), tags=(tag,))
        
        # Configurar colores para los tags
        self.tree.tag_configure('reciente', background='#e8f5e8')
        self.tree.tag_configure('medio', background='#fff3e0')
        self.tree.tag_configure('viejo', background='#ffebee')
        
        # Actualizar estadísticas
        self._actualizar_estadisticas(nodos)
    
    def _actualizar_estadisticas(self, nodos):
        """Actualiza las estadísticas"""
        stats = self.cliente_p2p.obtener_estadisticas_descubrimiento()
        
        # Calcular estadísticas adicionales
        if nodos:
            ips_unicas = len(set(nodo.ip_address for nodo in nodos))
            tiempo_promedio = sum(nodo.timestamp for nodo in nodos) / len(nodos)
            import datetime
            ultimo_descubrimiento = max(nodo.timestamp for nodo in nodos)
            ultimo_str = datetime.datetime.fromtimestamp(ultimo_descubrimiento).strftime("%H:%M:%S")
        else:
            ips_unicas = 0
            ultimo_str = "N/A"
        
        stats_texto = f"""🔢 Nodos totales: {stats.get('nodos_totales', 0)}
🔍 Descubridores activos: {stats.get('descubridores_activos', 0)}
🌐 IPs únicas: {ips_unicas}
⚙️ Algoritmos: {', '.join(stats.get('nodos_por_descubridor', {}).keys())}
📡 Último descubrimiento: {ultimo_str}
✅ Estado: {'🟢 Funcionando' if self.cliente_p2p.autodescubrimiento_habilitado else '🔴 Deshabilitado'}"""
        
        self.stats_text.delete(1.0, 'end')
        self.stats_text.insert(1.0, stats_texto)
        self.stats_text.config(state='disabled')  # Solo lectura
    
    def _actualizar_periodicamente(self):
        """Actualiza los datos periódicamente"""
        try:
            if self.ventana.winfo_exists():
                self._actualizar_datos()
                self.ventana.after(3000, self._actualizar_periodicamente)  # 3 segundos
        except tk.TclError:
            # La ventana fue cerrada
            pass