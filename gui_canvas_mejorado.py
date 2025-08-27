"""
Interfaz gráfica mejorada con Canvas para el crucigrama cooperativo
Versión corregida con mejor gestión de eventos, renderizado optimizado y robustez
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import threading
import time
import sys
import logging
from typing import Set, Tuple, Optional, Dict
from crucigrama_crdt import CrucigramaCRDT, Celda
from sincronizacion import ClienteP2P
from generador_crucigramas import GeneradorCrucigramas
from dialogos import AgregarPalabraDialog, GenerarPersonalizadoDialog, VentanaNodosDescubiertos


class CrucigramaCanvasMejorado:
    """Canvas optimizado y corregido para renderizar el crucigrama"""
    
    def __init__(self, parent, crucigrama: CrucigramaCRDT, callback_cambio):
        self.crucigrama = crucigrama
        self.callback_cambio = callback_cambio
        self.parent = parent
        
        # Configuración visual mejorada
        self.tamaño_celda = 35
        self.margen = 25
        self.color_fondo = "#FAFAFA"
        self.color_borde = "#424242"
        self.color_borde_grueso = "#1976D2"
        self.color_celda_negra = "#212121"
        self.color_celda_seleccionada = "#E3F2FD"
        self.color_celda_resaltada = "#FFF9C4"
        self.color_celda_hover = "#F3E5F5"
        self.color_numero = "#1976D2"
        self.color_autor = "#757575"
        self.color_letra = "#212121"
        
        # Estado de interacción mejorado
        self.celda_seleccionada: Optional[Tuple[int, int]] = None
        self.celda_hover: Optional[Tuple[int, int]] = None
        self.tiene_foco = False
        self.hover_timer = None
        
        # Sistema de renderizado optimizado
        self.celdas_sucias: Set[Tuple[int, int]] = set()
        self.renderizado_completo_pendiente = True
        self.elementos_canvas: Dict[Tuple[int, int], Dict] = {}
        
        # Crear canvas mejorado
        self.canvas = tk.Canvas(
            parent,
            bg=self.color_fondo,
            highlightthickness=2,
            highlightcolor=self.color_borde_grueso,
            highlightbackground="#E0E0E0",
            cursor="crosshair",
            relief='sunken',
            bd=1
        )
        
        # Calcular dimensiones
        self._calcular_dimensiones()
        
        # Configurar scrollbars mejoradas
        self._configurar_scrollbars()
        
        # Configurar eventos mejorados
        self._configurar_eventos()
        
        # Configurar logging
        self.logger = logging.getLogger(f"CrucigramaCanvas-{id(self)}")
        
        # Renderizado inicial
        self.marcar_todo_sucio()
        self.actualizar_canvas()
    
    def _calcular_dimensiones(self):
        """Calcula las dimensiones necesarias del canvas con mejor precisión"""
        self.offset_x = self.margen + 40  # Espacio para números de columna
        self.offset_y = self.margen + 40  # Espacio para números de fila
        
        self.ancho_grid = self.crucigrama.columnas * self.tamaño_celda
        self.alto_grid = self.crucigrama.filas * self.tamaño_celda
        
        self.ancho_total = self.ancho_grid + self.offset_x + self.margen
        self.alto_total = self.alto_grid + self.offset_y + self.margen
        
        # Configurar canvas con mejor sizing
        canvas_width = min(900, self.ancho_total)
        canvas_height = min(650, self.alto_total)
        
        self.canvas.configure(
            width=canvas_width,
            height=canvas_height,
            scrollregion=(0, 0, self.ancho_total, self.alto_total)
        )
    
    def _configurar_scrollbars(self):
        """Configura las scrollbars mejoradas"""
        # Frame contenedor para canvas y scrollbars
        self.container_frame = tk.Frame(self.parent)
        
        # Scrollbar vertical
        self.v_scrollbar = ttk.Scrollbar(
            self.container_frame, 
            orient='vertical', 
            command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # Scrollbar horizontal  
        self.h_scrollbar = ttk.Scrollbar(
            self.container_frame,
            orient='horizontal',
            command=self.canvas.xview
        )
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Grid layout mejorado
        self.container_frame.grid_rowconfigure(0, weight=1)
        self.container_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        self.container_frame.pack(fill='both', expand=True)
        
        # Eventos de scroll mejorados
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        # Para Linux
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.canvas.bind("<Shift-Button-4>", self._on_shift_mousewheel)
        self.canvas.bind("<Shift-Button-5>", self._on_shift_mousewheel)
    
    def _configurar_eventos(self):
        """Configura eventos mejorados con mejor manejo de foco"""
        # Eventos de mouse
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Enter>", self._on_enter)
        
        # Eventos de foco mejorados
        self.canvas.bind("<FocusIn>", self._on_focus_in)
        self.canvas.bind("<FocusOut>", self._on_focus_out)
        
        # Eventos de teclado directos en canvas
        self.canvas.bind("<KeyPress>", self._on_key_press)
        
        # Permitir que el canvas reciba foco
        self.canvas.focus_set()
        
        # Hacer el canvas focusable con tab
        self.canvas.bind("<Tab>", lambda e: "break")  # Prevenir tab navigation por ahora
    
    def _on_mousewheel(self, event):
        """Maneja scroll vertical mejorado"""
        try:
            if event.delta:
                delta = -1 * (event.delta / 120)
            else:
                delta = -1 if event.num == 4 else 1
            
            self.canvas.yview_scroll(int(delta), "units")
        except Exception as e:
            self.logger.error(f"Error en mousewheel: {e}")
    
    def _on_shift_mousewheel(self, event):
        """Maneja scroll horizontal con Shift+Wheel"""
        try:
            if event.delta:
                delta = -1 * (event.delta / 120)
            else:
                delta = -1 if event.num == 4 else 1
            
            self.canvas.xview_scroll(int(delta), "units")
        except Exception as e:
            self.logger.error(f"Error en shift mousewheel: {e}")
    
    def _on_focus_in(self, event):
        """Maneja cuando el canvas obtiene foco"""
        self.tiene_foco = True
        self.canvas.configure(highlightbackground=self.color_borde_grueso)
        if self.celda_seleccionada:
            self.marcar_celda_sucia(self.celda_seleccionada)
            self.actualizar_canvas()
    
    def _on_focus_out(self, event):
        """Maneja cuando el canvas pierde foco"""
        self.tiene_foco = False
        self.canvas.configure(highlightbackground="#E0E0E0")
    
    def _on_enter(self, event):
        """Maneja cuando el mouse entra al canvas"""
        self.canvas.focus_set()
    
    def _on_click(self, event):
        """Maneja clicks mejorado con mejor precisión"""
        try:
            self.canvas.focus_force()  # Forzar foco
            
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            fila, columna = self._pixel_a_celda(canvas_x, canvas_y)
            
            if self._es_celda_valida(fila, columna):
                celda = self.crucigrama.obtener_celda(fila, columna)
                
                # No seleccionar celdas negras
                if celda and celda.es_negra:
                    return
                
                # Deseleccionar celda anterior
                if self.celda_seleccionada:
                    self.marcar_celda_sucia(self.celda_seleccionada)
                
                # Seleccionar nueva celda
                self.celda_seleccionada = (fila, columna)
                self.marcar_celda_sucia((fila, columna))
                self.actualizar_canvas()
                
                # Hacer scroll para mantener visible
                self._scroll_a_celda(fila, columna)
                
        except Exception as e:
            self.logger.error(f"Error en click: {e}")
    
    def _on_right_click(self, event):
        """Maneja click derecho mejorado"""
        try:
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
                
                self.marcar_celda_sucia((fila, columna))
                self.actualizar_canvas()
                
        except Exception as e:
            self.logger.error(f"Error en click derecho: {e}")
    
    def _on_motion(self, event):
        """Maneja movimiento del mouse con debouncing mejorado"""
        try:
            # Cancelar timer anterior si existe
            if self.hover_timer:
                self.canvas.after_cancel(self.hover_timer)
            
            # Programar actualización con delay pequeño para evitar flickering
            self.hover_timer = self.canvas.after(50, lambda: self._procesar_hover(event))
            
        except Exception as e:
            self.logger.error(f"Error en motion: {e}")
    
    def _procesar_hover(self, event):
        """Procesa el hover con debouncing"""
        try:
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            fila, columna = self._pixel_a_celda(canvas_x, canvas_y)
            
            if self._es_celda_valida(fila, columna):
                nueva_hover = (fila, columna)
                
                if self.celda_hover != nueva_hover:
                    # Limpiar hover anterior
                    if self.celda_hover:
                        self.marcar_celda_sucia(self.celda_hover)
                    
                    # Establecer nuevo hover
                    self.celda_hover = nueva_hover
                    self.marcar_celda_sucia(nueva_hover)
                    self.actualizar_canvas()
            else:
                self._clear_hover()
                
        except Exception as e:
            self.logger.error(f"Error procesando hover: {e}")
    
    def _on_leave(self, event):
        """Maneja cuando el mouse sale del canvas"""
        self._clear_hover()
    
    def _clear_hover(self):
        """Limpia el estado de hover"""
        if self.celda_hover:
            self.marcar_celda_sucia(self.celda_hover)
            self.celda_hover = None
            self.actualizar_canvas()
        
        if self.hover_timer:
            self.canvas.after_cancel(self.hover_timer)
            self.hover_timer = None
    
    def _pixel_a_celda(self, x: float, y: float) -> Tuple[int, int]:
        """Convierte coordenadas de pixel a fila/columna con mejor precisión"""
        fila = int((y - self.offset_y) / self.tamaño_celda)
        columna = int((x - self.offset_x) / self.tamaño_celda)
        return fila, columna
    
    def _celda_a_pixel(self, fila: int, columna: int) -> Tuple[float, float]:
        """Convierte fila/columna a coordenadas de pixel"""
        x = self.offset_x + columna * self.tamaño_celda
        y = self.offset_y + fila * self.tamaño_celda
        return x, y
    
    def _es_celda_valida(self, fila: int, columna: int) -> bool:
        """Verifica si la celda está dentro del grid"""
        return (0 <= fila < self.crucigrama.filas and 
                0 <= columna < self.crucigrama.columnas)
    
    def _on_key_press(self, event):
        """Maneja entrada de teclado mejorada"""
        if not self.tiene_foco:
            return
        
        try:
            tecla = event.keysym
            char = event.char.upper() if event.char else ""
            
            # Manejo de selección inicial si no hay celda seleccionada
            if not self.celda_seleccionada and tecla in ['Up', 'Down', 'Left', 'Right']:
                self.celda_seleccionada = (0, 0)
                self.marcar_celda_sucia((0, 0))
                self.actualizar_canvas()
                return
            
            if not self.celda_seleccionada:
                return
            
            fila, columna = self.celda_seleccionada
            
            # Letras
            if char.isalpha() and len(char) == 1:
                self.callback_cambio(fila, columna, char)
                self.marcar_celda_sucia((fila, columna))
                self.actualizar_canvas()
                # Mover a siguiente celda horizontal
                self._mover_seleccion(0, 1)
                
            # Backspace/Delete
            elif tecla in ['BackSpace', 'Delete']:
                self.callback_cambio(fila, columna, None)
                self.marcar_celda_sucia((fila, columna))
                self.actualizar_canvas()
                if tecla == 'BackSpace':
                    self._mover_seleccion(0, -1)
                    
            # Espacios y números para limpiar
            elif tecla == 'space' or char.isdigit():
                self.callback_cambio(fila, columna, None)
                self.marcar_celda_sucia((fila, columna))
                self.actualizar_canvas()
                
            # Navegación con flechas
            elif tecla in ['Up', 'Down', 'Left', 'Right']:
                self._manejar_navegacion(tecla)
                
            # Escape para deseleccionar
            elif tecla == 'Escape':
                self._deseleccionar()
                
            # Enter/Return
            elif tecla in ['Return', 'KP_Enter']:
                # Mover a siguiente fila, misma columna
                self._mover_seleccion(1, 0)
                
            # Tab para moverse horizontal
            elif tecla == 'Tab':
                if event.state & 0x1:  # Shift+Tab
                    self._mover_seleccion(0, -1)
                else:
                    self._mover_seleccion(0, 1)
                
        except Exception as e:
            self.logger.error(f"Error en key press: {e}")
    
    def _manejar_navegacion(self, tecla: str):
        """Maneja navegación con teclado mejorada"""
        if not self.celda_seleccionada:
            return
        
        delta_map = {
            'Up': (-1, 0),
            'Down': (1, 0),
            'Left': (0, -1),
            'Right': (0, 1)
        }
        
        if tecla in delta_map:
            delta_fila, delta_columna = delta_map[tecla]
            self._mover_seleccion(delta_fila, delta_columna)
    
    def _mover_seleccion(self, delta_fila: int, delta_columna: int):
        """Mueve la selección con salto inteligente de celdas negras"""
        if not self.celda_seleccionada:
            return
        
        fila, columna = self.celda_seleccionada
        
        # Intentar mover hasta encontrar celda válida
        for intento in range(max(self.crucigrama.filas, self.crucigrama.columnas)):
            nueva_fila = fila + delta_fila * (intento + 1)
            nueva_columna = columna + delta_columna * (intento + 1)
            
            # Wrap around si está habilitado y llegamos al borde
            if nueva_fila < 0:
                nueva_fila = self.crucigrama.filas - 1
            elif nueva_fila >= self.crucigrama.filas:
                nueva_fila = 0
            
            if nueva_columna < 0:
                nueva_columna = self.crucigrama.columnas - 1
            elif nueva_columna >= self.crucigrama.columnas:
                nueva_columna = 0
            
            if not self._es_celda_valida(nueva_fila, nueva_columna):
                break
            
            # Verificar si la celda es válida (no negra)
            celda = self.crucigrama.obtener_celda(nueva_fila, nueva_columna)
            if not (celda and celda.es_negra):
                # Celda válida encontrada
                self.marcar_celda_sucia(self.celda_seleccionada)  # Limpiar anterior
                self.celda_seleccionada = (nueva_fila, nueva_columna)
                self.marcar_celda_sucia((nueva_fila, nueva_columna))  # Marcar nueva
                self.actualizar_canvas()
                self._scroll_a_celda(nueva_fila, nueva_columna)
                return
        
        # Si no encontramos celda válida, no mover
        self.logger.debug("No se encontró celda válida para mover")
    
    def _deseleccionar(self):
        """Deselecciona la celda actual"""
        if self.celda_seleccionada:
            self.marcar_celda_sucia(self.celda_seleccionada)
            self.celda_seleccionada = None
            self.actualizar_canvas()
    
    def _scroll_a_celda(self, fila: int, columna: int):
        """Hace scroll inteligente para mantener visible una celda"""
        try:
            x, y = self._celda_a_pixel(fila, columna)
            
            # Obtener dimensiones del viewport
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return  # Canvas no inicializado todavía
            
            # Obtener posición actual del scroll
            scroll_x = self.canvas.canvasx(0)
            scroll_y = self.canvas.canvasy(0)
            
            # Calcular si necesita scroll horizontal
            margen_scroll = self.tamaño_celda * 2  # Margen para que no quede en el borde
            
            if x < scroll_x + margen_scroll:
                # Scroll hacia la izquierda
                new_x = max(0, x - margen_scroll)
                self.canvas.xview_moveto(new_x / self.ancho_total)
            elif x + self.tamaño_celda > scroll_x + canvas_width - margen_scroll:
                # Scroll hacia la derecha
                new_x = min(self.ancho_total - canvas_width, 
                           x + self.tamaño_celda + margen_scroll - canvas_width)
                self.canvas.xview_moveto(new_x / self.ancho_total)
            
            # Calcular si necesita scroll vertical
            if y < scroll_y + margen_scroll:
                # Scroll hacia arriba
                new_y = max(0, y - margen_scroll)
                self.canvas.yview_moveto(new_y / self.alto_total)
            elif y + self.tamaño_celda > scroll_y + canvas_height - margen_scroll:
                # Scroll hacia abajo
                new_y = min(self.alto_total - canvas_height,
                           y + self.tamaño_celda + margen_scroll - canvas_height)
                self.canvas.yview_moveto(new_y / self.alto_total)
                
        except Exception as e:
            self.logger.error(f"Error en scroll a celda: {e}")
    
    def marcar_celda_sucia(self, celda: Tuple[int, int]):
        """Marca una celda como que necesita re-renderizado"""
        if self._es_celda_valida(celda[0], celda[1]):
            self.celdas_sucias.add(celda)
    
    def marcar_todo_sucio(self):
        """Marca que necesita renderizado completo"""
        self.renderizado_completo_pendiente = True
        self.celdas_sucias.clear()
    
    def actualizar_canvas(self):
        """Sistema de renderizado optimizado con dirty rectangles"""
        try:
            if self.renderizado_completo_pendiente:
                self._renderizado_completo()
                self.renderizado_completo_pendiente = False
                self.celdas_sucias.clear()
            elif self.celdas_sucias:
                self._renderizado_parcial()
                self.celdas_sucias.clear()
                
        except Exception as e:
            self.logger.error(f"Error actualizando canvas: {e}")
    
    def _renderizado_completo(self):
        """Renderiza todo el canvas desde cero"""
        self.canvas.delete("all")
        self.elementos_canvas.clear()
        
        # Dibujar números guía
        self._dibujar_numeros_guia()
        
        # Dibujar todas las celdas
        for fila in range(self.crucigrama.filas):
            for columna in range(self.crucigrama.columnas):
                self._dibujar_celda_completa(fila, columna)
    
    def _renderizado_parcial(self):
        """Renderiza solo las celdas que cambiaron"""
        for fila, columna in self.celdas_sucias:
            if self._es_celda_valida(fila, columna):
                self._actualizar_celda_existente(fila, columna)
    
    def _dibujar_numeros_guia(self):
        """Dibuja los números de guía mejorados"""
        # Números de columna
        for col in range(self.crucigrama.columnas):
            x = self.offset_x + col * self.tamaño_celda + self.tamaño_celda // 2
            y = self.offset_y - 15
            
            self.canvas.create_text(
                x, y, text=str(col),
                font=("Arial", 9, "bold"), fill=self.color_numero,
                tags="guia"
            )
        
        # Números de fila
        for fila in range(self.crucigrama.filas):
            x = self.offset_x - 15
            y = self.offset_y + fila * self.tamaño_celda + self.tamaño_celda // 2
            
            self.canvas.create_text(
                x, y, text=str(fila),
                font=("Arial", 9, "bold"), fill=self.color_numero,
                tags="guia"
            )
    
    def _dibujar_celda_completa(self, fila: int, columna: int):
        """Dibuja una celda completa con todos sus elementos"""
        x, y = self._celda_a_pixel(fila, columna)
        celda = self.crucigrama.obtener_celda(fila, columna)
        
        # Determinar color de fondo y borde
        color_fondo, color_borde, ancho_borde = self._obtener_colores_celda(fila, columna, celda)
        
        # Crear elementos de la celda
        elementos = {}
        
        # Rectángulo principal
        elementos['rect'] = self.canvas.create_rectangle(
            x, y, x + self.tamaño_celda, y + self.tamaño_celda,
            fill=color_fondo, outline=color_borde, width=ancho_borde,
            tags=f"celda_{fila}_{columna}"
        )
        
        # Contenido si no es celda negra
        if not (celda and celda.es_negra):
            # Número (esquina superior izquierda)
            if celda and celda.numero:
                elementos['numero'] = self.canvas.create_text(
                    x + 6, y + 8, text=str(celda.numero),
                    font=("Arial", 8, "bold"), fill=self.color_numero,
                    anchor='nw', tags=f"celda_{fila}_{columna}"
                )
            
            # Letra (centro)
            if celda and celda.letra:
                elementos['letra'] = self.canvas.create_text(
                    x + self.tamaño_celda // 2, y + self.tamaño_celda // 2,
                    text=celda.letra,
                    font=("Arial", 14, "bold"), fill=self.color_letra,
                    tags=f"celda_{fila}_{columna}"
                )
            
            # Autor (esquina inferior derecha)
            if celda and celda.autor:
                autor_texto = celda.autor[:3]
                elementos['autor'] = self.canvas.create_text(
                    x + self.tamaño_celda - 4, y + self.tamaño_celda - 4,
                    text=autor_texto, font=("Arial", 7), fill=self.color_autor,
                    anchor='se', tags=f"celda_{fila}_{columna}"
                )
        
        # Guardar elementos para actualización posterior
        self.elementos_canvas[(fila, columna)] = elementos
    
    def _actualizar_celda_existente(self, fila: int, columna: int):
        """Actualiza una celda existente eficientemente"""
        # Eliminar elementos existentes de esta celda
        if (fila, columna) in self.elementos_canvas:
            for elemento in self.elementos_canvas[(fila, columna)].values():
                try:
                    self.canvas.delete(elemento)
                except:
                    pass  # El elemento ya fue eliminado
        
        # Re-dibujar la celda
        self._dibujar_celda_completa(fila, columna)
    
    def _obtener_colores_celda(self, fila: int, columna: int, celda: Optional[Celda]) -> Tuple[str, str, int]:
        """Obtiene los colores apropiados para una celda"""
        # Celdas negras
        if celda and celda.es_negra:
            return self.color_celda_negra, self.color_borde, 1
        
        # Celda seleccionada (prioridad más alta)
        if self.celda_seleccionada == (fila, columna):
            if self.tiene_foco:
                return self.color_celda_seleccionada, self.color_borde_grueso, 3
            else:
                return self.color_celda_seleccionada, self.color_borde_grueso, 2
        
        # Celda hover
        if self.celda_hover == (fila, columna):
            return self.color_celda_hover, self.color_borde_grueso, 2
        
        # Celda normal
        return self.color_fondo, self.color_borde, 1
    
    def redimensionar(self):
        """Maneja redimensionamiento del canvas"""
        try:
            self._calcular_dimensiones()
            self.marcar_todo_sucio()
            self.actualizar_canvas()
        except Exception as e:
            self.logger.error(f"Error redimensionando: {e}")
    
    def limpiar(self):
        """Limpia recursos al cerrar"""
        try:
            if self.hover_timer:
                self.canvas.after_cancel(self.hover_timer)
            
            self.canvas.delete("all")
            self.elementos_canvas.clear()
            self.celdas_sucias.clear()
            
        except Exception as e:
            self.logger.error(f"Error limpiando canvas: {e}")


class CrucigramaCanvasGUIMejorado:
    """Interfaz principal mejorada usando Canvas optimizado"""
    
    def __init__(self):
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("CrucigramaGUI")
        
        try:
            self.root = tk.Tk()
            self.root.title("🎯 Crucigrama Cooperativo - Canvas Mejorado")
            self.root.geometry("1400x900")
            
            # Configuración de la ventana
            self.root.minsize(800, 600)
            
            # Maximizar en Windows
            if sys.platform == 'win32':
                try:
                    self.root.state('zoomed')
                except:
                    pass
            
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
            self.lock_actualizacion = threading.Lock()
            
            # Configurar interfaz
            self._configurar_interfaz()
            
            # Iniciar servicios
            self._iniciar_servicios()
            
            self.logger.info("Interfaz inicializada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando interfaz: {e}")
            raise
    
    def _solicitar_nombre_usuario(self):
        """Solicita el nombre del usuario con mejor diálogo"""
        while True:
            nombre = simpledialog.askstring(
                "👤 Identificación de Usuario", 
                "Ingresa tu nombre para el crucigrama cooperativo:",
                initialvalue="Usuario"
            )
            
            if nombre is None:  # Cancelar
                sys.exit()
            
            nombre = nombre.strip()
            if nombre:
                return nombre[:20]  # Limitar longitud
            
            messagebox.showwarning("Nombre Requerido", "Debes ingresar un nombre válido")
    
    def _configurar_interfaz(self):
        """Configura la interfaz principal mejorada"""
        # Configurar grid principal
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Panel superior mejorado
        self._crear_panel_info_mejorado()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#FAFAFA')
        main_frame.grid(row=1, column=0, sticky='nsew', padx=8, pady=8)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Frame para canvas (área principal)
        canvas_frame = tk.Frame(main_frame, relief='sunken', bd=2, bg='white')
        canvas_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Crear canvas del crucigrama mejorado
        self.crucigrama_canvas = CrucigramaCanvasMejorado(
            canvas_frame, self.crucigrama, self._on_celda_cambio
        )
        
        # Panel de controles mejorado (derecha)
        self._crear_panel_controles_mejorado(main_frame)
        
        # Configurar eventos de ventana
        self.root.bind('<Configure>', self._on_window_configure)
    
    def _crear_panel_info_mejorado(self):
        """Crea panel de información superior mejorado"""
        info_frame = tk.Frame(self.root, relief='raised', bd=2, bg='#E3F2FD', height=60)
        info_frame.grid(row=0, column=0, sticky='ew', padx=8, pady=(8, 0))
        info_frame.grid_propagate(False)
        
        # Frame izquierdo para info del usuario
        left_frame = tk.Frame(info_frame, bg='#E3F2FD')
        left_frame.pack(side='left', fill='y', padx=15, pady=10)
        
        tk.Label(
            left_frame,
            text=f"👤 {self.nombre_usuario}",
            font=('Arial', 13, 'bold'),
            bg='#E3F2FD',
            fg='#1976D2'
        ).pack(anchor='w')
        
        tk.Label(
            left_frame,
            text=f"🆔 {self.crucigrama.node_id}",
            font=('Arial', 9),
            bg='#E3F2FD',
            fg='#666666'
        ).pack(anchor='w')
        
        # Frame derecho para estado y controles
        right_frame = tk.Frame(info_frame, bg='#E3F2FD')
        right_frame.pack(side='right', fill='y', padx=15, pady=5)
        
        # Estado de conexión
        self.conexion_label = tk.Label(
            right_frame,
            text="🔄 Iniciando...",
            fg='#FF9800',
            font=('Arial', 11, 'bold'),
            bg='#E3F2FD'
        )
        self.conexion_label.pack(anchor='e', pady=(5, 0))
        
        # Botones de utilidad
        utils_frame = tk.Frame(right_frame, bg='#E3F2FD')
        utils_frame.pack(anchor='e')
        
        tk.Button(
            utils_frame,
            text="❓",
            font=('Arial', 10, 'bold'),
            command=self._mostrar_ayuda,
            width=3,
            bg='#FFC107',
            relief='raised'
        ).pack(side='right', padx=2)
        
        tk.Button(
            utils_frame,
            text="⚙️",
            font=('Arial', 10),
            command=self._mostrar_configuracion,
            width=3,
            bg='#9E9E9E',
            relief='raised'
        ).pack(side='right', padx=2)
    
    def _crear_panel_controles_mejorado(self, parent):
        """Crea panel de controles mejorado"""
        controles_frame = tk.Frame(parent, relief='sunken', bd=2, width=380, bg='#F5F5F5')
        controles_frame.grid(row=0, column=1, sticky='nsew')
        controles_frame.grid_propagate(False)
        
        # Scroll para el panel de controles
        canvas_controles = tk.Canvas(controles_frame, bg='#F5F5F5', highlightthickness=0)
        scrollbar_controles = ttk.Scrollbar(controles_frame, orient="vertical", command=canvas_controles.yview)
        scrollable_frame = tk.Frame(canvas_controles, bg='#F5F5F5')
        
        canvas_controles.configure(yscrollcommand=scrollbar_controles.set)
        canvas_controles.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Título mejorado
        titulo_frame = tk.Frame(scrollable_frame, bg='#1976D2', height=50)
        titulo_frame.pack(fill='x', pady=(0, 10))
        titulo_frame.pack_propagate(False)
        
        tk.Label(
            titulo_frame,
            text="🎮 Panel de Control",
            font=('Arial', 16, 'bold'),
            bg='#1976D2',
            fg='white'
        ).pack(expand=True)
        
        # Secciones del panel
        self._crear_seccion_acciones(scrollable_frame)
        self._crear_seccion_generacion_mejorada(scrollable_frame)
        self._crear_seccion_red(scrollable_frame)
        self._crear_seccion_palabras_mejorada(scrollable_frame)
        self._crear_seccion_estadisticas_mejorada(scrollable_frame)
        self._crear_seccion_log_mejorada(scrollable_frame)
        
        # Configurar scroll
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_controles.configure(scrollregion=canvas_controles.bbox("all"))
        )
        
        # Empaquetar elementos del scroll
        canvas_controles.pack(side="left", fill="both", expand=True)
        scrollbar_controles.pack(side="right", fill="y")
    
    def _crear_seccion_acciones(self, parent):
        """Crea sección de acciones principales"""
        frame = tk.LabelFrame(
            parent, 
            text="🎯 Acciones Principales", 
            font=('Arial', 12, 'bold'),
            bg='#F5F5F5',
            padx=10, pady=8
        )
        frame.pack(fill='x', padx=10, pady=5)
        
        botones = [
            ("➕ Agregar Palabra", self._agregar_palabra_dialog, "#4CAF50"),
            ("🗑️ Limpiar Todo", self._limpiar_crucigrama, "#F44336"),
        ]
        
        for texto, comando, color in botones:
            tk.Button(
                frame,
                text=texto,
                command=comando,
                font=('Arial', 11, 'bold'),
                bg=color,
                fg='white',
                relief='raised',
                bd=2,
                pady=5
            ).pack(fill='x', pady=3)
    
    def _crear_seccion_generacion_mejorada(self, parent):
        """Crea sección de generación automática mejorada"""
        frame = tk.LabelFrame(
            parent,
            text="🚀 Generación Automática",
            font=('Arial', 12, 'bold'),
            bg='#F5F5F5',
            padx=10, pady=8
        )
        frame.pack(fill='x', padx=10, pady=5)
        
        # Botones rápidos con colores
        botones_rapidos = [
            ("🟢 Fácil", "facil", "#8BC34A"),
            ("🟠 Difícil", "dificil", "#FF5722"),
            ("💻 Tecnología", "tecnologia", "#2196F3"),
            ("🧪 Ciencia", "ciencia", "#9C27B0"),
            ("🌍 Geografía", "geografia", "#4CAF50"),
            ("📚 Historia", "historia", "#795548")
        ]
        
        # Crear grid de botones
        for i, (texto, tipo, color) in enumerate(botones_rapidos):
            row = i // 2
            col = i % 2
            
            btn = tk.Button(
                frame,
                text=texto,
                command=lambda t=tipo: self._generar_crucigrama(t),
                font=('Arial', 10, 'bold'),
                bg=color,
                fg='white',
                width=15,
                pady=3
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
        
        # Configurar columnas
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        # Separador
        tk.Frame(frame, height=1, bg='#CCCCCC').grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
        
        # Botón personalizado destacado
        tk.Button(
            frame,
            text="⚙️ Personalizado",
            command=self._generar_personalizado_dialog,
            font=('Arial', 12, 'bold'),
            bg='#FF9800',
            fg='white',
            relief='raised',
            bd=3,
            pady=8
        ).grid(row=4, column=0, columnspan=2, sticky='ew', pady=5)
    
    def _crear_seccion_red(self, parent):
        """Crea sección de red y conectividad"""
        frame = tk.LabelFrame(
            parent,
            text="🌐 Red y Conectividad",
            font=('Arial', 12, 'bold'),
            bg='#F5F5F5',
            padx=10, pady=8
        )
        frame.pack(fill='x', padx=10, pady=5)
        
        botones_red = [
            ("🔍 Buscar Nodos", self._buscar_nodos, "#2196F3"),
            ("📊 Ver Estadísticas", self._mostrar_nodos_descubiertos, "#9C27B0")
        ]
        
        for texto, comando, color in botones_red:
            tk.Button(
                frame,
                text=texto,
                command=comando,
                font=('Arial', 10, 'bold'),
                bg=color,
                fg='white',
                pady=4
            ).pack(fill='x', pady=2)
    
    def _crear_seccion_palabras_mejorada(self, parent):
        """Crea sección de palabras mejorada"""
        frame = tk.LabelFrame(
            parent,
            text="📝 Palabras del Crucigrama",
            font=('Arial', 12, 'bold'),
            bg='#F5F5F5',
            padx=10, pady=8
        )
        frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Frame para listbox con scrollbar
        list_frame = tk.Frame(frame, bg='#F5F5F5')
        list_frame.pack(fill='both', expand=True, pady=5)
        
        # Listbox con mejor estilo
        self.palabras_listbox = tk.Listbox(
            list_frame,
            height=8,
            font=('Consolas', 9),
            bg='#FFFFFF',
            selectbackground='#E3F2FD',
            relief='sunken',
            bd=2
        )
        
        palabras_scrollbar = ttk.Scrollbar(list_frame, orient='vertical')
        self.palabras_listbox.configure(yscrollcommand=palabras_scrollbar.set)
        palabras_scrollbar.configure(command=self.palabras_listbox.yview)
        
        self.palabras_listbox.pack(side='left', fill='both', expand=True)
        palabras_scrollbar.pack(side='right', fill='y')
        
        # Binding para double-click
        self.palabras_listbox.bind('<Double-Button-1>', self._on_palabra_double_click)
    
    def _crear_seccion_estadisticas_mejorada(self, parent):
        """Crea sección de estadísticas mejorada"""
        frame = tk.LabelFrame(
            parent,
            text="📊 Estadísticas en Vivo",
            font=('Arial', 12, 'bold'),
            bg='#F5F5F5',
            padx=10, pady=8
        )
        frame.pack(fill='x', padx=10, pady=5)
        
        # Frame para estadísticas con mejor layout
        stats_inner = tk.Frame(frame, bg='#FFFFFF', relief='sunken', bd=1)
        stats_inner.pack(fill='x', pady=5)
        
        self.stats_label = tk.Label(
            stats_inner,
            text="Cargando estadísticas...",
            font=('Consolas', 10),
            justify='left',
            anchor='w',
            bg='#FFFFFF',
            padx=10,
            pady=5
        )
        self.stats_label.pack(fill='x')
    
    def _crear_seccion_log_mejorada(self, parent):
        """Crea sección de log mejorada"""
        frame = tk.LabelFrame(
            parent,
            text="📋 Log de Actividad",
            font=('Arial', 12, 'bold'),
            bg='#F5F5F5',
            padx=10, pady=8
        )
        frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Text widget con mejor estilo
        self.log_text = scrolledtext.ScrolledText(
            frame,
            height=8,
            width=35,
            font=('Consolas', 8),
            wrap='word',
            bg='#1E1E1E',
            fg='#00FF00',
            insertbackground='#00FF00',
            relief='sunken',
            bd=2
        )
        self.log_text.pack(fill='both', expand=True, pady=5)
        
        # Configurar tags para colores
        self.log_text.tag_configure("error", foreground="#FF5555")
        self.log_text.tag_configure("success", foreground="#50FA7B")
        self.log_text.tag_configure("info", foreground="#8BE9FD")
        self.log_text.tag_configure("warning", foreground="#FFB86C")
    
    def _on_window_configure(self, event):
        """Maneja redimensionamiento de ventana"""
        if event.widget == self.root:
            # Notificar al canvas que se redimensionó
            self.root.after_idle(lambda: self.crucigrama_canvas.redimensionar())
    
    def _on_celda_cambio(self, fila, columna, valor):
        """Maneja cambios en celdas con mejor logging"""
        try:
            if valor == 'NEGRA':
                self.crucigrama.establecer_celda_negra(fila, columna, self.nombre_usuario)
                self._log(f"🔲 Celda ({fila},{columna}) → negra", "info")
            elif valor is None:
                self.crucigrama.establecer_letra(fila, columna, None, self.nombre_usuario)
                self._log(f"🗑️ Celda ({fila},{columna}) → limpiada", "info")
            else:
                self.crucigrama.establecer_letra(fila, columna, valor, self.nombre_usuario)
                self._log(f"✏️ '{valor}' → ({fila},{columna})", "success")
            
            # Sincronizar cambios
            self.cliente_p2p.enviar_cambio_local()
            self._actualizar_estadisticas()
            
        except Exception as e:
            self.logger.error(f"Error en cambio de celda: {e}")
            self._log(f"❌ Error: {e}", "error")
    
    def _generar_crucigrama(self, tipo: str):
        """Genera crucigrama con mejor feedback"""
        try:
            if messagebox.askyesno(
                "🎯 Confirmar Generación",
                f"¿Generar crucigrama {tipo}?\n\n⚠️ Esto reemplazará el crucigrama actual."
            ):
                self._log(f"🚀 Generando crucigrama {tipo}...", "info")
                self.root.config(cursor="wait")
                self.root.update()
                
                if tipo == "facil":
                    nuevo_crucigrama = self.generador.generar_plantilla_facil()
                elif tipo == "dificil":
                    nuevo_crucigrama = self.generador.generar_plantilla_dificil()
                elif tipo in ["tecnologia", "ciencia", "geografia", "historia"]:
                    nuevo_crucigrama = self.generador.generar_crucigrama_tematico(tipo)
                else:
                    nuevo_crucigrama = self.generador.generar_crucigrama_basico()
                
                self._cargar_crucigrama_generado(nuevo_crucigrama)
                self._log(f"✅ Crucigrama {tipo} listo ({len(nuevo_crucigrama.palabras)} palabras)", "success")
                
                self.root.config(cursor="")
                
        except Exception as e:
            self.root.config(cursor="")
            self.logger.error(f"Error generando crucigrama: {e}")
            self._log(f"❌ Error generando: {e}", "error")
            messagebox.showerror("Error", f"Error generando crucigrama: {e}")
    
    def _cargar_crucigrama_generado(self, nuevo_crucigrama):
        """Carga crucigrama generado con mejor manejo"""
        try:
            # Limpiar crucigrama actual
            self.crucigrama = CrucigramaCRDT(15, 15, self.nombre_usuario)
            
            # Cargar palabras
            for numero, palabra in nuevo_crucigrama.palabras.items():
                self.crucigrama.agregar_palabra(
                    palabra.pista,
                    palabra.respuesta,
                    palabra.fila_inicio,
                    palabra.columna_inicio,
                    palabra.direccion,
                    self.nombre_usuario
                )
            
            # Actualizar canvas y referencias
            self.crucigrama_canvas.crucigrama = self.crucigrama
            self.crucigrama_canvas.marcar_todo_sucio()
            self.crucigrama_canvas.actualizar_canvas()
            
            # Actualizar interfaz
            self._actualizar_palabras_lista()
            self._actualizar_estadisticas()
            
            # Sincronizar
            self.cliente_p2p.crucigrama = self.crucigrama
            self.cliente_p2p.enviar_cambio_local()
            
        except Exception as e:
            self.logger.error(f"Error cargando crucigrama: {e}")
            raise
    
    def _agregar_palabra_dialog(self):
        """Abre diálogo para agregar palabra"""
        try:
            AgregarPalabraDialog(self.root, self._on_palabra_agregada)
        except Exception as e:
            self.logger.error(f"Error abriendo diálogo: {e}")
            self._log(f"❌ Error abriendo diálogo: {e}", "error")
    
    def _on_palabra_agregada(self, pista, respuesta, fila, columna, direccion):
        """Callback mejorado cuando se agrega palabra"""
        try:
            numero = self.crucigrama.agregar_palabra(
                pista, respuesta, fila, columna, direccion, self.nombre_usuario
            )
            
            if numero:
                self._log(f"✅ '{respuesta}' agregada (#{numero})", "success")
                self.crucigrama_canvas.marcar_todo_sucio()
                self.crucigrama_canvas.actualizar_canvas()
                self._actualizar_palabras_lista()
                self.cliente_p2p.enviar_cambio_local()
            else:
                self._log(f"❌ No se pudo agregar '{respuesta}'", "error")
                messagebox.showerror("Error", "No se pudo agregar la palabra")
                
        except Exception as e:
            self.logger.error(f"Error agregando palabra: {e}")
            self._log(f"❌ Error: {e}", "error")
    
    def _generar_personalizado_dialog(self):
        """Diálogo para crucigrama personalizado"""
        try:
            GenerarPersonalizadoDialog(self.root, self._on_crucigrama_personalizado)
        except Exception as e:
            self.logger.error(f"Error abriendo diálogo personalizado: {e}")
            self._log(f"❌ Error: {e}", "error")
    
    def _on_crucigrama_personalizado(self, categoria, num_palabras, dificultad):
        """Callback para crucigrama personalizado"""
        try:
            self._log(f"🎨 Generando personalizado: {categoria}, {num_palabras} palabras", "info")
            self.root.config(cursor="wait")
            
            if categoria == "mixto":
                crucigrama = self.generador.generar_crucigrama_basico(num_palabras=num_palabras)
            else:
                crucigrama = self.generador.generar_crucigrama_tematico(categoria)
            
            self._cargar_crucigrama_generado(crucigrama)
            self._log(f"✅ Crucigrama personalizado listo", "success")
            self.root.config(cursor="")
            
        except Exception as e:
            self.root.config(cursor="")
            self.logger.error(f"Error crucigrama personalizado: {e}")
            self._log(f"❌ Error: {e}", "error")
            messagebox.showerror("Error", f"Error: {e}")
    
    def _buscar_nodos(self):
        """Busca nodos con mejor feedback"""
        try:
            if self.cliente_p2p.autodescubrimiento_habilitado:
                self._log("🔍 Buscando nodos...", "info")
                nodos = self.cliente_p2p.obtener_nodos_descubiertos()
                
                if nodos:
                    self.conexion_label.config(text=f"🟢 Conectado ({len(nodos)})", fg='#4CAF50')
                    self._log(f"📡 Encontrados {len(nodos)} nodos:", "success")
                    for nodo in nodos:
                        self._log(f"  👤 {nodo.nombre_usuario} ({nodo.ip_address})", "info")
                else:
                    self._log("❌ No se encontraron nodos", "warning")
                    self.conexion_label.config(text="🔴 Sin conexiones", fg='#F44336')
            else:
                self._log("❌ Autodescubrimiento deshabilitado", "error")
                
        except Exception as e:
            self.logger.error(f"Error buscando nodos: {e}")
            self._log(f"❌ Error: {e}", "error")
    
    def _mostrar_nodos_descubiertos(self):
        """Muestra ventana de nodos descubiertos"""
        try:
            VentanaNodosDescubiertos(self.root, self.cliente_p2p)
        except Exception as e:
            self.logger.error(f"Error mostrando nodos: {e}")
            self._log(f"❌ Error: {e}", "error")
    
    def _limpiar_crucigrama(self):
        """Limpia todo el crucigrama con confirmación"""
        try:
            if messagebox.askyesno(
                "🗑️ Confirmar Limpieza", 
                "¿Estás seguro de limpiar todo el crucigrama?\n\n⚠️ Esta acción no se puede deshacer."
            ):
                self.crucigrama = CrucigramaCRDT(15, 15, self.nombre_usuario)
                self.crucigrama_canvas.crucigrama = self.crucigrama
                self.crucigrama_canvas.marcar_todo_sucio()
                self.crucigrama_canvas.actualizar_canvas()
                self._actualizar_palabras_lista()
                self._log("🗑️ Crucigrama limpiado", "warning")
                
        except Exception as e:
            self.logger.error(f"Error limpiando crucigrama: {e}")
            self._log(f"❌ Error: {e}", "error")
    
    def _mostrar_ayuda(self):
        """Muestra ventana de ayuda mejorada"""
        ayuda = """
🎯 CRUCIGRAMA COOPERATIVO - GUÍA COMPLETA

🖱️ CONTROLES DEL CANVAS:
• Click izquierdo: Seleccionar celda
• Click derecho: Marcar/desmarcar celda negra  
• Teclear letras: Escribir en celda seleccionada
• Flechas ←↑→↓: Navegar entre celdas
• Enter: Moverse a fila siguiente
• Tab: Moverse horizontal
• Backspace: Borrar y retroceder
• Delete/Espacio: Solo borrar
• Escape: Deseleccionar celda

⚡ GENERACIÓN AUTOMÁTICA:
• Botones temáticos para crucigramas específicos
• Personalizado para configuración avanzada
• Más de 100 palabras en 6 categorías
• Algoritmo inteligente de colocación

🌐 COLABORACIÓN:
• Autodescubrimiento automático de usuarios
• Sincronización en tiempo real
• Resolución automática de conflictos
• Cada celda muestra su autor

📝 FUNCIONES AVANZADAS:
• Scroll inteligente con rueda del mouse
• Hover visual sobre celdas
• Colores diferentes según estado
• Log con código de colores
• Estadísticas en tiempo real

🔧 SHORTCUTS:
• Ctrl+N: Nuevo crucigrama
• Ctrl+S: Guardar (próximamente)
• F5: Actualizar vista
• F11: Pantalla completa

💡 TIPS:
• Las celdas negras se saltan automáticamente
• El canvas se adapta al tamaño de ventana
• Los cambios se sincronizan automáticamente
• Usa el panel derecho para generar contenido
        """
        
        ventana_ayuda = tk.Toplevel(self.root)
        ventana_ayuda.title("❓ Ayuda - Crucigrama Cooperativo")
        ventana_ayuda.geometry("600x700")
        ventana_ayuda.resizable(True, True)
        ventana_ayuda.transient(self.root)
        
        # Centrar ventana
        ventana_ayuda.update_idletasks()
        x = (ventana_ayuda.winfo_screenwidth() // 2) - (ventana_ayuda.winfo_width() // 2)
        y = (ventana_ayuda.winfo_screenheight() // 2) - (ventana_ayuda.winfo_height() // 2)
        ventana_ayuda.geometry(f"+{x}+{y}")
        
        # Text widget con scroll
        text_frame = tk.Frame(ventana_ayuda)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap='word',
            font=('Arial', 11),
            padx=15,
            pady=15,
            bg='#FAFAFA'
        )
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', ayuda)
        text_widget.config(state='disabled')
        
        # Botón cerrar
        tk.Button(
            ventana_ayuda,
            text="✅ Entendido",
            command=ventana_ayuda.destroy,
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            pady=8
        ).pack(pady=10)
    
    def _mostrar_configuracion(self):
        """Muestra diálogo de configuración"""
        messagebox.showinfo(
            "⚙️ Configuración",
            "Panel de configuración próximamente...\n\n"
            "Por ahora puedes:\n"
            "• Ajustar tamaño de ventana\n"
            "• Usar el panel de controles\n"
            "• Personalizar generación automática"
        )
    
    def _on_palabra_double_click(self, event):
        """Maneja double-click en lista de palabras"""
        try:
            selection = self.palabras_listbox.curselection()
            if selection:
                # Obtener información de la palabra seleccionada
                index = selection[0]
                palabras_ordenadas = sorted(self.crucigrama.palabras.items())
                if index < len(palabras_ordenadas):
                    numero, palabra = palabras_ordenadas[index]
                    
                    # Ir a la palabra en el canvas
                    self.crucigrama_canvas.celda_seleccionada = (palabra.fila_inicio, palabra.columna_inicio)
                    self.crucigrama_canvas.marcar_celda_sucia((palabra.fila_inicio, palabra.columna_inicio))
                    self.crucigrama_canvas._scroll_a_celda(palabra.fila_inicio, palabra.columna_inicio)
                    self.crucigrama_canvas.actualizar_canvas()
                    
                    self._log(f"📍 Navegando a palabra #{numero}: {palabra.respuesta}", "info")
                    
        except Exception as e:
            self.logger.error(f"Error en double-click: {e}")
    
    def _actualizar_palabras_lista(self):
        """Actualiza la lista de palabras con mejor formato"""
        try:
            self.palabras_listbox.delete(0, 'end')
            for numero, palabra in sorted(self.crucigrama.palabras.items()):
                direccion_symbol = "→" if palabra.direccion == "horizontal" else "↓"
                texto = f"{numero:2}. {direccion_symbol} {palabra.respuesta:12} ({palabra.fila_inicio},{palabra.columna_inicio})"
                self.palabras_listbox.insert('end', texto)
        except Exception as e:
            self.logger.error(f"Error actualizando lista palabras: {e}")
    
    def _actualizar_estadisticas(self):
        """Actualiza estadísticas con mejor formato"""
        try:
            with self.lock_actualizacion:
                num_palabras = len(self.crucigrama.palabras)
                celdas_ocupadas = sum(
                    1 for f in range(self.crucigrama.filas)
                    for c in range(self.crucigrama.columnas)
                    if self.crucigrama.obtener_celda(f, c) and 
                       (self.crucigrama.obtener_celda(f, c).letra or 
                        self.crucigrama.obtener_celda(f, c).es_negra)
                )
                
                nodos_conectados = len(self.cliente_p2p.obtener_nodos_descubiertos())
                
                # Calcular completitud aproximada
                total_celdas = self.crucigrama.filas * self.crucigrama.columnas
                completitud = (celdas_ocupadas / total_celdas) * 100
                
                stats_texto = f"""📊 Palabras: {num_palabras}
📱 Celdas: {celdas_ocupadas}/{total_celdas}
📈 Completitud: {completitud:.1f}%
🌐 Nodos: {nodos_conectados}
👤 Usuario: {self.nombre_usuario[:12]}
🆔 ID: {self.crucigrama.node_id[:8]}..."""
                
                self.stats_label.config(text=stats_texto)
                
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas: {e}")
    
    def _log(self, mensaje: str, tipo: str = "info"):
        """Agrega mensaje al log con colores"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            
            # Mapeo de tipos a emojis y tags
            tipos_config = {
                "info": ("ℹ️", "info"),
                "success": ("✅", "success"), 
                "error": ("❌", "error"),
                "warning": ("⚠️", "warning")
            }
            
            emoji, tag = tipos_config.get(tipo, ("📝", "info"))
            
            mensaje_completo = f"[{timestamp}] {emoji} {mensaje}\n"
            
            self.log_text.insert('end', mensaje_completo, tag)
            self.log_text.see('end')
            
            # Limitar tamaño del log (mantener últimas 100 líneas)
            lines = self.log_text.get("1.0", 'end').count('\n')
            if lines > 100:
                self.log_text.delete("1.0", f"{lines-100}.0")
                
        except Exception as e:
            self.logger.error(f"Error en log: {e}")
    
    def _iniciar_servicios(self):
        """Inicia todos los servicios"""
        try:
            # Iniciar autodescubrimiento
            if self.cliente_p2p.autodescubrimiento_habilitado:
                self.cliente_p2p.iniciar_autodescubrimiento()
                self._log("🚀 Sistema iniciado correctamente", "success")
                self.conexion_label.config(text="🔍 Buscando...", fg='#FF9800')
            else:
                self._log("⚠️ Autodescubrimiento deshabilitado", "warning")
            
            # Iniciar actualización automática
            self._iniciar_actualizacion_automatica()
            
        except Exception as e:
            self.logger.error(f"Error iniciando servicios: {e}")
            self._log(f"❌ Error iniciando servicios: {e}", "error")
    
    def _iniciar_actualizacion_automatica(self):
        """Inicia actualización automática mejorada"""
        def actualizar():
            while self.actualizacion_automatica:
                try:
                    self.root.after(0, self._actualizar_periodica)
                    time.sleep(5)  # Actualizar cada 5 segundos (reducido de 2)
                except Exception as e:
                    self.logger.error(f"Error en actualización automática: {e}")
                    break
        
        thread = threading.Thread(target=actualizar, daemon=True)
        thread.start()
        self.logger.info("Actualización automática iniciada")
    
    def _actualizar_periodica(self):
        """Actualización periódica de la interfaz"""
        try:
            # Solo actualizar si hay cambios o cada cierto tiempo
            self._actualizar_palabras_lista()
            self._actualizar_estadisticas()
            
            # Verificar conexiones de red
            nodos = self.cliente_p2p.obtener_nodos_descubiertos()
            if nodos:
                if "Conectado" not in self.conexion_label.cget("text"):
                    self.conexion_label.config(text=f"🟢 Conectado ({len(nodos)})", fg='#4CAF50')
            else:
                if "Sin conexiones" not in self.conexion_label.cget("text"):
                    self.conexion_label.config(text="🔴 Sin conexiones", fg='#F44336')
                    
        except Exception as e:
            self.logger.error(f"Error en actualización periódica: {e}")
    
    def ejecutar(self):
        """Ejecuta la aplicación con mejor manejo de errores"""
        try:
            self._log("🎮 Crucigrama Cooperativo iniciado", "success")
            self._log(f"👤 Usuario: {self.nombre_usuario}", "info")
            
            # Configurar cierre
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Configurar bindings globales
            self.root.bind('<F5>', lambda e: self._actualizar_forzada())
            self.root.bind('<F1>', lambda e: self._mostrar_ayuda())
            
            # Iniciar loop principal
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error ejecutando aplicación: {e}")
            messagebox.showerror("Error Fatal", f"Error ejecutando aplicación: {e}")
    
    def _actualizar_forzada(self):
        """Actualización forzada con F5"""
        try:
            self._log("🔄 Actualizando vista...", "info")
            self.crucigrama_canvas.marcar_todo_sucio()
            self.crucigrama_canvas.actualizar_canvas()
            self._actualizar_palabras_lista()
            self._actualizar_estadisticas()
            self._log("✅ Vista actualizada", "success")
        except Exception as e:
            self.logger.error(f"Error en actualización forzada: {e}")
            self._log(f"❌ Error actualizando: {e}", "error")
    
    def _on_closing(self):
        """Maneja el cierre de la aplicación con limpieza"""
        try:
            self._log("🛑 Cerrando aplicación...", "warning")
            
            # Detener actualización automática
            self.actualizacion_automatica = False
            
            # Detener servicios de red
            self.cliente_p2p.detener_sync()
            
            # Limpiar canvas
            self.crucigrama_canvas.limpiar()
            
            # Cerrar ventana
            self.root.quit()
            self.root.destroy()
            
            self.logger.info("Aplicación cerrada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error cerrando aplicación: {e}")
            self.root.destroy()


def main():
    """Función principal con mejor manejo de errores"""
    try:
        app = CrucigramaCanvasGUIMejorado()
        app.ejecutar()
    except KeyboardInterrupt:
        print("\nAplicación cancelada por el usuario")
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
        
        # Intentar fallback
        try:
            print("\nIntentando versión de respaldo...")
            from gui_crucigrama import CrucigramaGUI
            app_fallback = CrucigramaGUI()
            app_fallback.ejecutar()
        except Exception as e2:
            print(f"Error también en versión de respaldo: {e2}")


if __name__ == "__main__":
    main()