#!/usr/bin/env python3
"""
Interfaz gráfica para el chat cooperativo con lista de nodos
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any
from chat_crdt import ChatCRDT, Mensaje
from sincronizacion_chat import ClienteP2PChat
from descubrimiento_nodos import InfoNodo


class ChatGUI:
    """Interfaz gráfica principal del chat cooperativo"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("💬 Chat Cooperativo - CRDT")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Datos del usuario
        nombre_usuario = simpledialog.askstring("Usuario", "Ingresa tu nombre de usuario:")
        if not nombre_usuario:
            nombre_usuario = "Usuario_Anónimo"
            
        self.usuario_id = nombre_usuario
        self.chat = ChatCRDT(self.usuario_id)
        self.chat.establecer_callback_cambio(self._actualizar_interfaz)
        
        # Estado de la interfaz - usando canal único
        self.canal_actual = "chat"
        self.mensaje_seleccionado = None
        
        # Cliente P2P
        self.cliente_p2p = ClienteP2PChat(
            self.chat,
            nombre_usuario=nombre_usuario,
            habilitar_autodescubrimiento=True
        )
        
        # Configurar callbacks para nodos
        self.cliente_p2p.establecer_callbacks_nodos(
            self._nodo_conectado,
            self._nodo_desconectado
        )
        
        self._crear_interfaz()
        
        # Iniciar cliente P2P
        self.cliente_p2p.iniciar()
        
        # Mensaje de bienvenida
        self.chat.enviar_mensaje(f"🎉 {nombre_usuario} se ha unido al chat!")
        
    def _crear_interfaz(self):
        """Crea la interfaz principal"""
        # Frame principal con tres paneles
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel izquierdo - Lista de nodos y canales
        self._crear_panel_lateral(main_paned)
        
        # Panel central - Chat principal
        self._crear_panel_chat(main_paned)
        
        # Panel derecho - Información y estadísticas
        self._crear_panel_info(main_paned)
        
        # Barra de estado
        self._crear_barra_estado()
        
    def _crear_panel_lateral(self, parent):
        """Crea el panel lateral con nodos y canales"""
        panel_lateral = ttk.Frame(parent)
        parent.add(panel_lateral, weight=1)
        
        # Notebook para pestañas
        notebook = ttk.Notebook(panel_lateral)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña de nodos conectados
        self._crear_pestaña_nodos(notebook)
        
        # Pestaña de chat único - simplificado
        self._crear_pestaña_chat_unico(notebook)
        
    def _crear_pestaña_nodos(self, parent):
        """Crea la pestaña de nodos conectados"""
        frame_nodos = ttk.Frame(parent)
        parent.add(frame_nodos, text="🌐 Nodos")
        
        # Título
        ttk.Label(frame_nodos, text="Nodos Descubiertos", 
                 font=("Arial", 12, "bold")).pack(pady=(5, 10))
        
        # Lista de nodos
        list_frame = ttk.Frame(frame_nodos)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        self.listbox_nodos = tk.Listbox(list_frame, font=("Arial", 10))
        scrollbar_nodos = ttk.Scrollbar(list_frame, orient="vertical", 
                                      command=self.listbox_nodos.yview)
        self.listbox_nodos.configure(yscrollcommand=scrollbar_nodos.set)
        
        self.listbox_nodos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_nodos.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Información del nodo local
        info_frame = ttk.LabelFrame(frame_nodos, text="Mi Información", padding="5")
        info_frame.pack(fill=tk.X, padx=5, pady=(10, 5))
        
        self.label_mi_info = tk.Label(info_frame, text="", font=("Arial", 9), 
                                     justify=tk.LEFT, anchor=tk.W)
        self.label_mi_info.pack(fill=tk.X)
        
        # Botones de nodos
        button_frame = ttk.Frame(frame_nodos)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="🔄 Actualizar", 
                  command=self._actualizar_lista_nodos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="ℹ️ Detalles", 
                  command=self._mostrar_detalles_nodo).pack(side=tk.LEFT)
        
    def _crear_pestaña_chat_unico(self, parent):
        """Crea la pestaña del chat único"""
        frame_chat_info = ttk.Frame(parent)
        parent.add(frame_chat_info, text="💬 Chat")
        
        # Título
        ttk.Label(frame_chat_info, text="Chat Único", 
                 font=("Arial", 12, "bold")).pack(pady=(5, 10))
        
        # Información del chat
        info_frame = ttk.LabelFrame(frame_chat_info, text="Información", padding="10")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.label_chat_info = tk.Label(info_frame, text="", font=("Arial", 9), 
                                       justify=tk.LEFT, anchor=tk.W)
        self.label_chat_info.pack(fill=tk.X)
        
        # Controles del chat
        control_frame = ttk.LabelFrame(frame_chat_info, text="Controles", padding="10")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="🔄 Actualizar Chat", 
                  command=self._actualizar_chat_info).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(control_frame, text="🧹 Limpiar Vista", 
                  command=self._limpiar_chat).pack(fill=tk.X)
        
    def _crear_panel_chat(self, parent):
        """Crea el panel principal de chat"""
        panel_chat = ttk.Frame(parent)
        parent.add(panel_chat, weight=3)
        
        # Título del chat único
        self.label_canal = tk.Label(panel_chat, text="💬 Chat Cooperativo", 
                                   font=("Arial", 14, "bold"))
        self.label_canal.pack(pady=(5, 10))
        
        # Área de mensajes
        self._crear_area_mensajes(panel_chat)
        
        # Área de entrada de texto
        self._crear_area_entrada(panel_chat)
        
    def _crear_area_mensajes(self, parent):
        """Crea el área de visualización de mensajes"""
        messages_frame = ttk.LabelFrame(parent, text="Mensajes", padding="5")
        messages_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Text widget con scrollbar
        text_frame = ttk.Frame(messages_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_mensajes = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10), 
                                   state=tk.DISABLED, bg="#f5f5f5")
        scrollbar_mensajes = ttk.Scrollbar(text_frame, orient="vertical", 
                                         command=self.text_mensajes.yview)
        self.text_mensajes.configure(yscrollcommand=scrollbar_mensajes.set)
        
        self.text_mensajes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_mensajes.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar tags para colores
        self.text_mensajes.tag_configure("usuario_local", foreground="#0066cc", font=("Arial", 10, "bold"))
        self.text_mensajes.tag_configure("usuario_remoto", foreground="#cc6600", font=("Arial", 10, "bold"))
        self.text_mensajes.tag_configure("timestamp", foreground="#666666", font=("Arial", 8))
        self.text_mensajes.tag_configure("sistema", foreground="#009900", font=("Arial", 10, "italic"))
        self.text_mensajes.tag_configure("eliminado", foreground="#999999", font=("Arial", 10, "italic"))
        
        # Botones de mensajes
        msg_buttons_frame = ttk.Frame(messages_frame)
        msg_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(msg_buttons_frame, text="🔍 Buscar", 
                  command=self._buscar_mensajes).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(msg_buttons_frame, text="🗑️ Limpiar", 
                  command=self._limpiar_chat).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(msg_buttons_frame, text="📋 Exportar", 
                  command=self._exportar_chat).pack(side=tk.LEFT)
        
    def _crear_area_entrada(self, parent):
        """Crea el área de entrada de texto"""
        entrada_frame = ttk.LabelFrame(parent, text="Escribir mensaje", padding="5")
        entrada_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Frame para texto y botones
        input_frame = ttk.Frame(entrada_frame)
        input_frame.pack(fill=tk.X)
        
        # Entry para escribir mensajes
        self.entry_mensaje = tk.Text(input_frame, height=2, wrap=tk.WORD, 
                                   font=("Arial", 11))
        self.entry_mensaje.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Botones
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(buttons_frame, text="📤 Enviar", 
                  command=self._enviar_mensaje).pack(fill=tk.X, pady=(0, 2))
        ttk.Button(buttons_frame, text="😊 Emoji", 
                  command=self._insertar_emoji).pack(fill=tk.X)
        
        # Bind Enter para enviar
        self.entry_mensaje.bind("<Control-Return>", lambda e: self._enviar_mensaje())
        self.entry_mensaje.focus()
        
    def _crear_panel_info(self, parent):
        """Crea el panel de información y estadísticas"""
        panel_info = ttk.Frame(parent)
        parent.add(panel_info, weight=1)
        
        # Notebook para pestañas
        notebook_info = ttk.Notebook(panel_info)
        notebook_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña de estadísticas
        self._crear_pestaña_estadisticas(notebook_info)
        
        # Pestaña de usuarios activos
        self._crear_pestaña_usuarios(notebook_info)
        
    def _crear_pestaña_estadisticas(self, parent):
        """Crea la pestaña de estadísticas"""
        frame_stats = ttk.Frame(parent)
        parent.add(frame_stats, text="📊 Stats")
        
        # Título
        ttk.Label(frame_stats, text="Estadísticas", 
                 font=("Arial", 12, "bold")).pack(pady=(5, 10))
        
        # Área de estadísticas
        self.text_stats = tk.Text(frame_stats, height=10, font=("Arial", 9), 
                                state=tk.DISABLED, bg="#f9f9f9")
        self.text_stats.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Botón actualizar
        ttk.Button(frame_stats, text="🔄 Actualizar", 
                  command=self._actualizar_estadisticas).pack(pady=5)
        
    def _crear_pestaña_usuarios(self, parent):
        """Crea la pestaña de usuarios activos"""
        frame_usuarios = ttk.Frame(parent)
        parent.add(frame_usuarios, text="👥 Usuarios")
        
        # Título
        ttk.Label(frame_usuarios, text="Usuarios Activos", 
                 font=("Arial", 12, "bold")).pack(pady=(5, 10))
        
        # Lista de usuarios
        self.listbox_usuarios = tk.Listbox(frame_usuarios, font=("Arial", 10))
        self.listbox_usuarios.pack(fill=tk.BOTH, expand=True, padx=5)
        
    def _crear_barra_estado(self):
        """Crea la barra de estado"""
        self.barra_estado = ttk.Label(self.root, text="Conectado", relief=tk.SUNKEN)
        self.barra_estado.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
        
    def _enviar_mensaje(self):
        """Envía un mensaje al chat"""
        contenido = self.entry_mensaje.get("1.0", tk.END).strip()
        if not contenido:
            return
        
        # Enviar mensaje al canal único
        mensaje_id = self.chat.enviar_mensaje(contenido)
        
        if mensaje_id:
            # Limpiar entrada
            self.entry_mensaje.delete("1.0", tk.END)
            
            # Actualizar interfaz
            self._actualizar_mensajes()
            
            # Scroll hacia abajo
            self.text_mensajes.see(tk.END)
            
            self.barra_estado.config(text=f"Mensaje enviado")
        
    def _insertar_emoji(self):
        """Inserta un emoji en el mensaje"""
        emojis = ["😊", "😂", "❤️", "👍", "👎", "🎉", "🔥", "💯", "🚀", "⭐"]
        
        # Crear ventana simple de selección
        emoji_window = tk.Toplevel(self.root)
        emoji_window.title("Seleccionar Emoji")
        emoji_window.geometry("300x200")
        emoji_window.transient(self.root)
        emoji_window.grab_set()
        
        # Frame de emojis
        frame = ttk.Frame(emoji_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Botones de emojis
        for i, emoji in enumerate(emojis):
            row = i // 5
            col = i % 5
            ttk.Button(frame, text=emoji, width=3,
                      command=lambda e=emoji: self._seleccionar_emoji(e, emoji_window)).grid(
                row=row, col=col, padx=2, pady=2)
        
    def _seleccionar_emoji(self, emoji, ventana):
        """Selecciona un emoji e inserta en el mensaje"""
        self.entry_mensaje.insert(tk.INSERT, emoji)
        ventana.destroy()
        self.entry_mensaje.focus()
        
    def _buscar_mensajes(self):
        """Busca mensajes en el chat"""
        query = simpledialog.askstring("Buscar", "Ingresa texto a buscar:")
        if not query:
            return
        
        resultados = self.chat.buscar_mensajes(query)
        
        if not resultados:
            messagebox.showinfo("Búsqueda", "No se encontraron mensajes")
            return
        
        # Mostrar resultados en ventana nueva
        self._mostrar_resultados_busqueda(resultados, query)
        
    def _mostrar_resultados_busqueda(self, resultados: List[Mensaje], query: str):
        """Muestra los resultados de búsqueda"""
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Resultados: '{query}' ({len(resultados)} encontrados)")
        ventana.geometry("600x400")
        
        # Text widget para mostrar resultados
        text_frame = ttk.Frame(ventana, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_resultados = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_resultados.yview)
        text_resultados.configure(yscrollcommand=scrollbar.set)
        
        text_resultados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Agregar resultados
        for i, mensaje in enumerate(resultados):
            if i > 0:
                text_resultados.insert(tk.END, "\n" + "─" * 50 + "\n")
            
            fecha_str = mensaje.timestamp.strftime("%d/%m %H:%M")
            header = f"[{fecha_str}] {mensaje.autor} en #{mensaje.canal}:\n"
            text_resultados.insert(tk.END, header)
            text_resultados.insert(tk.END, mensaje.contenido + "\n")
        
        text_resultados.config(state=tk.DISABLED)
        
    def _limpiar_chat(self):
        """Limpia la visualización del chat"""
        if messagebox.askyesno("Limpiar", "¿Limpiar la visualización del chat?"):
            self.text_mensajes.config(state=tk.NORMAL)
            self.text_mensajes.delete("1.0", tk.END)
            self.text_mensajes.config(state=tk.DISABLED)
            
    def _exportar_chat(self):
        """Exporta el chat actual"""
        from tkinter import filedialog
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if archivo:
            try:
                import json
                data = self.chat.exportar_chat()
                with open(archivo, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Exportar", f"Chat exportado a {archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {e}")
                
    def _actualizar_chat_info(self):
        """Actualiza información del chat único"""
        stats = self.chat.obtener_estadisticas()
        usuarios_activos = self.chat.obtener_usuarios_activos()
        
        info_texto = f"Canal: #{self.canal_actual}\n"
        info_texto += f"Mensajes totales: {stats['total_mensajes']}\n"
        info_texto += f"Mensajes hoy: {stats['mensajes_hoy']}\n"
        info_texto += f"Usuarios activos: {len(usuarios_activos)}"
        
        self.label_chat_info.config(text=info_texto)
            
    def _cambiar_canal(self, event):
        """Método mantenido para compatibilidad - no hace nada en canal único"""
        pass
            
    def _actualizar_lista_nodos(self):
        """Actualiza la lista de nodos descubiertos"""
        self.listbox_nodos.delete(0, tk.END)
        
        nodos = self.cliente_p2p.obtener_nodos_descubiertos()
        
        if not nodos:
            self.listbox_nodos.insert(tk.END, "🔍 Buscando nodos...")
        else:
            for nodo in nodos:
                estado = "🟢" if nodo.node_id in self.cliente_p2p.conexiones_activas else "🔴"
                texto = f"{estado} {nodo.nombre_usuario} ({nodo.ip_address}:{nodo.puerto})"
                self.listbox_nodos.insert(tk.END, texto)
        
        # Actualizar información personal
        stats_conexion = self.cliente_p2p.obtener_estadisticas_conexion()
        info_texto = f"Usuario: {self.usuario_id}\n"
        info_texto += f"Puerto: {stats_conexion['puerto_local']}\n"
        info_texto += f"Nodos: {stats_conexion['nodos_conocidos']}\n"
        info_texto += f"Conexiones: {stats_conexion['conexiones_activas']}"
        
        self.label_mi_info.config(text=info_texto)
        
    def _actualizar_lista_canales(self):
        """Actualiza información del canal único"""
        self._actualizar_chat_info()
                
    def _actualizar_mensajes(self):
        """Actualiza la visualización de mensajes"""
        mensajes = self.chat.obtener_mensajes_canal(self.canal_actual)
        
        self.text_mensajes.config(state=tk.NORMAL)
        self.text_mensajes.delete("1.0", tk.END)
        
        for mensaje in mensajes:
            # Timestamp
            fecha_str = mensaje.timestamp.strftime("%H:%M")
            self.text_mensajes.insert(tk.END, f"[{fecha_str}] ", "timestamp")
            
            # Autor
            if mensaje.autor == self.usuario_id:
                tag = "usuario_local"
            else:
                tag = "usuario_remoto"
            
            self.text_mensajes.insert(tk.END, f"{mensaje.autor}: ", tag)
            
            # Contenido
            if "[Mensaje eliminado]" in mensaje.contenido:
                self.text_mensajes.insert(tk.END, mensaje.contenido + "\n", "eliminado")
            elif mensaje.contenido.startswith("🎉"):
                self.text_mensajes.insert(tk.END, mensaje.contenido + "\n", "sistema")
            else:
                self.text_mensajes.insert(tk.END, mensaje.contenido + "\n")
        
        self.text_mensajes.config(state=tk.DISABLED)
        self.text_mensajes.see(tk.END)
        
    def _actualizar_estadisticas(self):
        """Actualiza las estadísticas"""
        stats = self.chat.obtener_estadisticas()
        stats_conexion = self.cliente_p2p.obtener_estadisticas_conexion()
        
        texto = f"📊 ESTADÍSTICAS DEL CHAT\n\n"
        texto += f"Mensajes totales: {stats['total_mensajes']}\n"
        texto += f"Mensajes hoy: {stats['mensajes_hoy']}\n"
        texto += f"Canales activos: {stats['canales_activos']}\n"
        texto += f"Usuarios activos: {stats['usuarios_activos']}\n\n"
        
        texto += f"🌐 CONEXIÓN P2P\n\n"
        texto += f"Puerto local: {stats_conexion['puerto_local']}\n"
        texto += f"Nodos conocidos: {stats_conexion['nodos_conocidos']}\n"
        texto += f"Conexiones activas: {stats_conexion['conexiones_activas']}\n"
        texto += f"Autodescubrimiento: {'🟢' if stats_conexion['autodescubrimiento_activo'] else '🔴'}\n\n"
        
        texto += f"👤 INFORMACIÓN PERSONAL\n\n"
        texto += f"Usuario: {self.usuario_id}\n"
        texto += f"Canal actual: #{self.canal_actual}\n"
        texto += f"Conectado desde: {datetime.now().strftime('%H:%M')}\n"
        
        self.text_stats.config(state=tk.NORMAL)
        self.text_stats.delete("1.0", tk.END)
        self.text_stats.insert("1.0", texto)
        self.text_stats.config(state=tk.DISABLED)
        
    def _actualizar_usuarios_activos(self):
        """Actualiza la lista de usuarios activos"""
        usuarios = self.chat.obtener_usuarios_activos()
        
        self.listbox_usuarios.delete(0, tk.END)
        
        for usuario in usuarios:
            estado = "🟢" if usuario in [n.nombre_usuario for n in self.cliente_p2p.obtener_nodos_descubiertos()] else "⚪"
            if usuario == self.usuario_id:
                estado = "👤"  # Usuario actual
            
            self.listbox_usuarios.insert(tk.END, f"{estado} {usuario}")
            
    def _mostrar_detalles_nodo(self):
        """Muestra detalles del nodo seleccionado"""
        selection = self.listbox_nodos.curselection()
        if not selection:
            messagebox.showinfo("Info", "Selecciona un nodo para ver detalles")
            return
        
        nodos = self.cliente_p2p.obtener_nodos_descubiertos()
        if selection[0] < len(nodos):
            nodo = nodos[selection[0]]
            
            detalles = f"INFORMACIÓN DEL NODO\n\n"
            detalles += f"Nombre: {nodo.nombre_usuario}\n"
            detalles += f"ID: {nodo.node_id}\n"
            detalles += f"IP: {nodo.ip_address}\n"
            detalles += f"Puerto: {nodo.puerto}\n"
            detalles += f"Tipo: {nodo.tipo_aplicacion}\n"
            detalles += f"Versión: {nodo.version_protocolo}\n\n"
            
            messagebox.showinfo(f"Detalles: {nodo.nombre_usuario}", detalles)
            
    def _nodo_conectado(self, nodo: InfoNodo):
        """Callback cuando se conecta un nodo"""
        self.root.after(0, lambda: [
            self._actualizar_lista_nodos(),
            self.barra_estado.config(text=f"Nodo conectado: {nodo.nombre_usuario}")
        ])
        
    def _nodo_desconectado(self, nodo: InfoNodo):
        """Callback cuando se desconecta un nodo"""
        self.root.after(0, lambda: [
            self._actualizar_lista_nodos(),
            self.barra_estado.config(text=f"Nodo desconectado: {nodo.nombre_usuario}")
        ])
        
    def _actualizar_interfaz(self):
        """Callback para actualizar la interfaz cuando cambia el CRDT"""
        self.root.after(0, lambda: [
            self._actualizar_mensajes(),
            self._actualizar_chat_info(),
            self._actualizar_usuarios_activos(),
            self._actualizar_estadisticas()
        ])
        
    def ejecutar(self):
        """Ejecuta la aplicación"""
        # Actualizar interfaz inicial
        self._actualizar_lista_nodos()
        self._actualizar_chat_info()
        self._actualizar_estadisticas()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar_aplicacion)
        
        # Bucle principal
        self.root.mainloop()
        
    def _cerrar_aplicacion(self):
        """Cierra la aplicación"""
        # Mensaje de despedida
        try:
            self.chat.enviar_mensaje(f"👋 {self.usuario_id} ha salido del chat.")
            time.sleep(1)  # Dar tiempo para sincronizar
        except:
            pass
        
        # Detener cliente P2P
        self.cliente_p2p.detener()
        
        # Cerrar ventana
        self.root.quit()
        self.root.destroy()


def main():
    """Función principal"""
    try:
        app = ChatGUI()
        app.ejecutar()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()