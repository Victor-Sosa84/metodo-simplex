"""
gui.py
------
Interfaz grafica del programa Metodo Simplex.
Tres pestanas: Minimizacion | Maximizacion | Dualidad

Llama a minimizacion.py y dualidad.py para la logica.
maximizacion.py se integra cuando este disponible.

Proyecto: Metodo Simplex — IO1, Semestre 1 - 2026, FICCT - UAGRM 
"""

import tkinter as tk
from tkinter import ttk, messagebox

from minimizacion import simplex_gran_m
from dualidad import convertir_dual, formatear_dual

# maximizacion se importa cuando este disponible
try:
    from maximizacion import simplex_maximizacion
    MAXIMIZACION_DISPONIBLE = True
except ImportError:
    MAXIMIZACION_DISPONIBLE = False


# ─────────────────────────────────────────
#  CONSTANTES DE ESTILO
# ─────────────────────────────────────────

FONT_TITULO  = ("Segoe UI", 16, "bold")
FONT_NORMAL  = ("Segoe UI", 12)
FONT_BOLD    = ("Segoe UI", 12, "bold")
FONT_MONO    = ("Courier New", 12)

COLOR_FONDO      = "#f4f4f4"
COLOR_FRAME      = "#ffffff"
COLOR_BTN        = "#2c7be5"
COLOR_BTN_TEXT   = "#ffffff"
COLOR_RESULTADO  = "#f0f7ff"
COLOR_ERROR      = "#fff0f0"
COLOR_BORDE      = "#d0d7de"

PAD = 14


# ─────────────────────────────────────────
#  WIDGET REUTILIZABLE: Tabla de entrada
#  (Filas de coeficientes)
# ─────────────────────────────────────────

class TablaCoeficientes(tk.Frame):
    """
    Grilla editable de m filas x n columnas.
    Usada para ingresar la matriz A de restricciones.
    """

    def __init__(self, parent, filas, columnas, encabezados=None, **kwargs):
        super().__init__(parent, bg=COLOR_FRAME, **kwargs)
        self.filas = filas
        self.columnas = columnas
        self.celdas = []

        # Encabezados de columnas
        if encabezados:
            for j, enc in enumerate(encabezados):
                tk.Label(self, text=enc, font=FONT_BOLD,
                        bg=COLOR_FRAME, fg="#555").grid(
                    row=0, column=j+1, padx=3, pady=2)

        for i in range(filas):
            fila_celdas = []
            tk.Label(self, text=f"R{i+1}", font=FONT_BOLD,
                    bg=COLOR_FRAME, fg="#555").grid(
                row=i+1, column=0, padx=4, pady=2)

            for j in range(columnas):
                entry = tk.Entry(self, width=11, font=FONT_NORMAL,
                                justify="center", relief="solid",
                                bd=1)
                entry.insert(0, "0")
                entry.grid(row=i+1, column=j+1, padx=2, pady=2)
                fila_celdas.append(entry)
            self.celdas.append(fila_celdas)

    def get_matriz(self):
        """Devuelve la matriz como list[list[float]]. Lanza ValueError si hay celda invalida."""
        matriz = []
        for i, fila in enumerate(self.celdas):
            fila_vals = []
            for j, entry in enumerate(fila):
                try:
                    fila_vals.append(float(entry.get()))
                except ValueError:
                    raise ValueError(f"Valor invalido en fila {i+1}, columna {j+1}.")
            matriz.append(fila_vals)
        return matriz

    def set_valor(self, i, j, valor):
        self.celdas[i][j].delete(0, tk.END)
        self.celdas[i][j].insert(0, str(valor))


# ─────────────────────────────────────────
#  PESTANA: MINIMIZACION
# ─────────────────────────────────────────

class PestanaMinimizacion(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_FONDO)
        self._n_vars = 0
        self._n_rest = 0
        self._tabla_A = None
        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []
        self._entries_nombres_rest = []
        self._construir_ui()

    def _construir_ui(self):
        # ── Panel izquierdo: configuracion ───────────────────────────────
        frame_config = tk.Frame(self, bg=COLOR_FONDO)
        frame_config.pack(side=tk.LEFT, fill=tk.Y, padx=PAD, pady=PAD)

        tk.Label(frame_config, text="Minimizacion",
                font=FONT_TITULO, bg=COLOR_FONDO).pack(anchor="w")
        tk.Label(frame_config,
                text="Metodo Simplex con Gran M",
                font=FONT_NORMAL, bg=COLOR_FONDO, fg="#666").pack(anchor="w", pady=(0, 10))

        # Cantidad de variables y restricciones
        frame_dim = tk.LabelFrame(frame_config, text="Dimensiones",
                                font=FONT_BOLD, bg=COLOR_FRAME,
                                padx=8, pady=6)
        frame_dim.pack(fill=tk.X, pady=(0, 8))

        tk.Label(frame_dim, text="Variables:", font=FONT_NORMAL,
                bg=COLOR_FRAME).grid(row=0, column=0, sticky="w", pady=2)
        self._spin_vars = tk.Spinbox(frame_dim, from_=1, to=20, width=5,
                                    font=FONT_NORMAL)
        self._spin_vars.delete(0, tk.END)
        self._spin_vars.insert(0, "6")
        self._spin_vars.grid(row=0, column=1, padx=6, pady=2)

        tk.Label(frame_dim, text="Restricciones:", font=FONT_NORMAL,
                bg=COLOR_FRAME).grid(row=1, column=0, sticky="w", pady=2)
        self._spin_rest = tk.Spinbox(frame_dim, from_=1, to=20, width=5,
                                    font=FONT_NORMAL)
        self._spin_rest.delete(0, tk.END)
        self._spin_rest.insert(0, "5")
        self._spin_rest.grid(row=1, column=1, padx=6, pady=2)

        tk.Button(frame_dim, text="Generar tabla",
                font=FONT_BOLD, bg=COLOR_BTN, fg=COLOR_BTN_TEXT,
                relief="flat", padx=8, pady=4,
                command=self._generar_tabla).grid(
            row=2, column=0, columnspan=2, pady=(8, 2))

        # Boton cargar ejemplo vacas
        tk.Button(frame_config, text="Cargar ejemplo: Vacas Lecheras",
                font=FONT_NORMAL, bg="#e8f0fe", fg="#1a56db",
                relief="flat", padx=6, pady=3,
                command=self._cargar_vacas).pack(fill=tk.X, pady=(0, 6))

        # Boton resolver
        tk.Button(frame_config, text="▶  Resolver",
                font=FONT_BOLD, bg="#1a7f37", fg=COLOR_BTN_TEXT,
                relief="flat", padx=10, pady=6,
                command=self._resolver).pack(fill=tk.X, pady=(4, 0))

        # ── Panel derecho: tabla de datos + resultado ─────────────────────
        frame_derecho = tk.Frame(self, bg=COLOR_FONDO)
        frame_derecho.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                        padx=(0, PAD), pady=PAD)

        # Contenedor scrollable para la tabla de entrada
        self._frame_tabla = tk.LabelFrame(frame_derecho, text="Datos del problema",
                                        font=FONT_BOLD, bg=COLOR_FRAME,
                                        padx=8, pady=6, height=320)
        self._frame_tabla.pack_propagate(False)
        self._frame_tabla.pack(fill=tk.X, expand=False)

        tk.Label(self._frame_tabla,
                text="Presiona 'Generar tabla' para ingresar los datos.",
                font=FONT_NORMAL, bg=COLOR_FRAME, fg="#888").pack(pady=20)

        # Resultado
        self._frame_resultado = tk.LabelFrame(frame_derecho, text="Resultado",
                                            font=FONT_BOLD, bg=COLOR_RESULTADO,
                                            padx=8, pady=6)
        self._frame_resultado.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        self._txt_resultado = tk.Text(self._frame_resultado, height=12,
                                    font=FONT_MONO, bg=COLOR_RESULTADO,
                                    relief="flat", state=tk.DISABLED,
                                    wrap=tk.WORD)
        self._txt_resultado.pack(fill=tk.BOTH, expand=True)

    def _generar_tabla(self):
        try:
            n = int(self._spin_vars.get())
            m = int(self._spin_rest.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa numeros validos de variables y restricciones.")
            return

        if n < 1 or m < 1:
            messagebox.showerror("Error", "Debe haber al menos 1 variable y 1 restriccion.")
            return

        self._n_vars = n
        self._n_rest = m

        # Limpiar frame tabla
        for widget in self._frame_tabla.winfo_children():
            widget.destroy()

        # Canvas + scrollbar para tabla grande
        canvas = tk.Canvas(self._frame_tabla, bg=COLOR_FRAME,
                        highlightthickness=0)
        scrollbar_v = ttk.Scrollbar(self._frame_tabla, orient="vertical",
                                    command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(self._frame_tabla, orient="horizontal",
                                    command=canvas.xview)
        canvas.configure(yscrollcommand=scrollbar_v.set,
                        xscrollcommand=scrollbar_h.set)

        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame_inner = tk.Frame(canvas, bg=COLOR_FRAME)
        canvas.create_window((0, 0), window=frame_inner, anchor="nw")
        frame_inner.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))

        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []
        self._entries_nombres_rest = []

        col_offset = 2  # columnas 0=etiqueta restriccion, 1=nombre restriccion

        # ── Fila 0: nombres de variables ─────────────────────────────────
        tk.Label(frame_inner, text="", bg=COLOR_FRAME).grid(
            row=0, column=0, columnspan=2)
        for j in range(n):
            e = tk.Entry(frame_inner, width=11, font=FONT_BOLD,
                        justify="center", relief="solid", bd=1, fg="#1a56db")
            e.insert(0, f"x{j+1}")
            e.grid(row=0, column=col_offset + j, padx=2, pady=2)
            self._entries_nombres_vars.append(e)

        tk.Label(frame_inner, text="b", font=FONT_BOLD,
                bg=COLOR_FRAME, fg="#555").grid(
            row=0, column=col_offset + n, padx=6)
        tk.Label(frame_inner, text="Tipo", font=FONT_BOLD,
                bg=COLOR_FRAME, fg="#555").grid(
            row=0, column=col_offset + n + 1, padx=4)

        # ── Fila 1: coeficientes de la funcion objetivo ───────────────────
        tk.Label(frame_inner, text="Min Z", font=FONT_BOLD,
                bg=COLOR_FRAME, fg="#1a7f37").grid(
            row=1, column=0, padx=4, sticky="w")
        tk.Label(frame_inner, text="(F. Objetivo)", font=FONT_NORMAL,
                bg=COLOR_FRAME, fg="#888").grid(row=1, column=1, padx=2)

        for j in range(n):
            e = tk.Entry(frame_inner, width=11, font=FONT_NORMAL,
                        justify="center", relief="solid", bd=1)
            e.insert(0, "0")
            e.grid(row=1, column=col_offset + j, padx=2, pady=2)
            self._entries_c.append(e)

        # ── Filas 2..m+1: restricciones ───────────────────────────────────
        for i in range(m):
            tk.Label(frame_inner, text=f"R{i+1}", font=FONT_BOLD,
                    bg=COLOR_FRAME, fg="#555").grid(
                row=i+2, column=0, padx=4, sticky="w")

            e_nombre = tk.Entry(frame_inner, width=14, font=FONT_NORMAL,
                                relief="solid", bd=1, fg="#555")
            e_nombre.insert(0, f"Restriccion {i+1}")
            e_nombre.grid(row=i+2, column=1, padx=2, pady=2)
            self._entries_nombres_rest.append(e_nombre)

        self._tabla_A = TablaCoeficientes(frame_inner, m, n)
        self._tabla_A.grid(row=2, column=col_offset,
                        rowspan=m, columnspan=n, padx=0, pady=0)

        for i in range(m):
            e_b = tk.Entry(frame_inner, width=11, font=FONT_NORMAL,
                        justify="center", relief="solid", bd=1)
            e_b.insert(0, "0")
            e_b.grid(row=i+2, column=col_offset + n, padx=6, pady=2)
            self._entries_b.append(e_b)

            combo = ttk.Combobox(frame_inner, values=["<=", ">=", "="],
                                width=4, font=FONT_NORMAL, state="readonly")
            combo.set(">=")
            combo.grid(row=i+2, column=col_offset + n + 1, padx=4, pady=2)
            self._combos_tipo.append(combo)

    def _cargar_vacas(self):
        """Precarga los datos del problema de vacas lecheras."""
        self._spin_vars.delete(0, tk.END)
        self._spin_vars.insert(0, "6")
        self._spin_rest.delete(0, tk.END)
        self._spin_rest.insert(0, "5")
        self._generar_tabla()

        nombres_vars = ["Maiz", "Sorgo", "T.Soya", "Afrechillo", "Alfalfa", "Hna.Hueso"]
        c_vals       = [2300, 2000, 3200, 1350, 1650, 4000]
        A_vals = [
            [1,    1,    1,    1,    1,    1   ],
            [90,   100,  440,  150,  180,  0   ],
            [3300, 3150, 3200, 2450, 2100, 0   ],
            [25,   28,   60,   110,  250,  0   ],
            [0.2,  0.4,  2.5,  1.2,  14,   300 ],
        ]
        b_vals   = [1, 160, 2600, 180, 6]
        tipos    = ["=", ">=", ">=", ">=", ">="]
        nombres_rest = [
            "Balance masa",
            "Proteina >= 160",
            "Energia >= 2600",
            "Fibra >= 180",
            "Calcio >= 6",
        ]

        for j, (nv, cv) in enumerate(zip(nombres_vars, c_vals)):
            self._entries_nombres_vars[j].delete(0, tk.END)
            self._entries_nombres_vars[j].insert(0, nv)
            self._entries_c[j].delete(0, tk.END)
            self._entries_c[j].insert(0, str(cv))

        for i, (fila, bv, tipo, nr) in enumerate(
                zip(A_vals, b_vals, tipos, nombres_rest)):
            for j, coef in enumerate(fila):
                self._tabla_A.set_valor(i, j, coef)
            self._entries_b[i].delete(0, tk.END)
            self._entries_b[i].insert(0, str(bv))
            self._combos_tipo[i].set(tipo)
            self._entries_nombres_rest[i].delete(0, tk.END)
            self._entries_nombres_rest[i].insert(0, nr)

    def _resolver(self):
        if self._tabla_A is None:
            messagebox.showwarning("Aviso", "Primero genera la tabla de datos.")
            return

        try:
            c     = [float(e.get()) for e in self._entries_c]
            b     = [float(e.get()) for e in self._entries_b]
            tipos = [cb.get() for cb in self._combos_tipo]
            A     = self._tabla_A.get_matriz()
            nombres_vars = [e.get() for e in self._entries_nombres_vars]
            nombres_rest = [e.get() for e in self._entries_nombres_rest]
        except ValueError as err:
            messagebox.showerror("Error de entrada", str(err))
            return

        # Validar b >= 0
        for i, bv in enumerate(b):
            if bv < 0:
                messagebox.showerror(
                    "Error", f"El valor b de la restriccion {i+1} es negativo.\n"
                            "Multiplica la restriccion por -1 e invierte el tipo.")
                return

        resultado = simplex_gran_m(c, A, b, tipos)
        self._mostrar_resultado(resultado, c, nombres_vars, nombres_rest, tipos, b)

    def _mostrar_resultado(self, res, c, nombres_vars, nombres_rest, tipos, b):
        self._txt_resultado.config(state=tk.NORMAL, bg=COLOR_RESULTADO)
        self._txt_resultado.delete("1.0", tk.END)

        lineas = []

        if res['estado'] == 'optimo':
            lineas.append("SOLUCION OPTIMA ENCONTRADA")
            lineas.append("=" * 40)
            lineas.append(f"Iteraciones: {res['iteraciones']}")
            lineas.append("")
            lineas.append("Variables:")
            for nombre, valor in zip(nombres_vars, res['x']):
                lineas.append(f"  {nombre:<18} = {valor:.6f}")
            lineas.append("")
            lineas.append(f"Costo minimo (Z) = {res['z']:,.4f}")

            # Verificar restricciones
            import numpy as np
            A_arr = [[float(v) for v in fila]
                    for fila in self._tabla_A.get_matriz()]
            lineas.append("")
            lineas.append("Verificacion de restricciones:")
            for i, (nombre, tipo, bv) in enumerate(zip(nombres_rest, tipos, b)):
                val = sum(A_arr[i][j] * res['x'][j] for j in range(len(res['x'])))
                lineas.append(f"  {nombre}: {val:.4f} {tipo} {bv}  ✓")

        elif res['estado'] == 'no_factible':
            self._txt_resultado.config(bg=COLOR_ERROR)
            lineas.append("SIN SOLUCION FACTIBLE")
            lineas.append("=" * 40)
            lineas.append(res['mensaje'])
            lineas.append("")
            lineas.append("Posibles causas:")
            lineas.append("  - Restricciones contradictorias entre si.")
            lineas.append("  - Algun valor minimo requerido es muy alto.")
            lineas.append("")
            lineas.append("Sugerencia: revisa los valores de b (lado derecho)")
            lineas.append("y verifica que las restricciones sean compatibles.")

        elif res['estado'] == 'no_acotado':
            self._txt_resultado.config(bg=COLOR_ERROR)
            lineas.append("PROBLEMA NO ACOTADO")
            lineas.append("=" * 40)
            lineas.append(res['mensaje'])

        self._txt_resultado.insert(tk.END, "\n".join(lineas))
        self._txt_resultado.config(state=tk.DISABLED)


# ─────────────────────────────────────────
#  PESTANA: MAXIMIZACION
# ─────────────────────────────────────────

class PestanaMaximizacion(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_FONDO)
        self._n_vars = 0
        self._n_rest = 0
        self._tabla_A = None
        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []
        self._entries_nombres_rest = []
        self._construir_ui()

    def _construir_ui(self):
        if not MAXIMIZACION_DISPONIBLE:
            tk.Label(self,
                    text="maximizacion.py aun no esta disponible.\n\n"
                        "Agrega el archivo al proyecto y reinicia el programa.",
                    font=FONT_NORMAL, bg=COLOR_FONDO, fg="#888",
                    justify="center").pack(expand=True)
            return

        # ── Panel izquierdo ───────────────────────────────────────────────
        frame_config = tk.Frame(self, bg=COLOR_FONDO)
        frame_config.pack(side=tk.LEFT, fill=tk.Y, padx=PAD, pady=PAD)

        tk.Label(frame_config, text="Maximizacion",
                font=FONT_TITULO, bg=COLOR_FONDO).pack(anchor="w")
        tk.Label(frame_config, text="Metodo Simplex estandar",
                font=FONT_NORMAL, bg=COLOR_FONDO, fg="#666").pack(
            anchor="w", pady=(0, 10))

        frame_dim = tk.LabelFrame(frame_config, text="Dimensiones",
                                font=FONT_BOLD, bg=COLOR_FRAME,
                                padx=8, pady=6)
        frame_dim.pack(fill=tk.X, pady=(0, 8))

        tk.Label(frame_dim, text="Variables:", font=FONT_NORMAL,
                bg=COLOR_FRAME).grid(row=0, column=0, sticky="w", pady=2)
        self._spin_vars = tk.Spinbox(frame_dim, from_=1, to=20, width=5,
                                    font=FONT_NORMAL)
        self._spin_vars.delete(0, tk.END)
        self._spin_vars.insert(0, "2")
        self._spin_vars.grid(row=0, column=1, padx=6, pady=2)

        tk.Label(frame_dim, text="Restricciones:", font=FONT_NORMAL,
                bg=COLOR_FRAME).grid(row=1, column=0, sticky="w", pady=2)
        self._spin_rest = tk.Spinbox(frame_dim, from_=1, to=20, width=5,
                                    font=FONT_NORMAL)
        self._spin_rest.delete(0, tk.END)
        self._spin_rest.insert(0, "2")
        self._spin_rest.grid(row=1, column=1, padx=6, pady=2)

        tk.Button(frame_dim, text="Generar tabla",
                  font=FONT_BOLD, bg=COLOR_BTN, fg=COLOR_BTN_TEXT,
                  relief="flat", padx=8, pady=4,
                  command=self._generar_tabla).grid(
            row=2, column=0, columnspan=2, pady=(8, 2))

        tk.Button(frame_config, text="▶  Resolver",
                  font=FONT_BOLD, bg="#1a7f37", fg=COLOR_BTN_TEXT,
                  relief="flat", padx=10, pady=6,
                  command=self._resolver).pack(fill=tk.X, pady=(4, 0))

        # ── Panel derecho ─────────────────────────────────────────────────
        frame_derecho = tk.Frame(self, bg=COLOR_FONDO)
        frame_derecho.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                           padx=(0, PAD), pady=PAD)

        self._frame_tabla = tk.LabelFrame(frame_derecho, text="Datos del problema",
                                          font=FONT_BOLD, bg=COLOR_FRAME,
                                          padx=8, pady=6, height=320)
        self._frame_tabla.pack_propagate(False)
        self._frame_tabla.pack(fill=tk.X, expand=False)

        tk.Label(self._frame_tabla,
                 text="Presiona 'Generar tabla' para ingresar los datos.",
                 font=FONT_NORMAL, bg=COLOR_FRAME, fg="#888").pack(pady=20)

        self._frame_resultado = tk.LabelFrame(frame_derecho, text="Resultado",
                                              font=FONT_BOLD, bg=COLOR_RESULTADO,
                                              padx=8, pady=6)
        self._frame_resultado.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        self._txt_resultado = tk.Text(self._frame_resultado, height=12,
                                      font=FONT_MONO, bg=COLOR_RESULTADO,
                                      relief="flat", state=tk.DISABLED,
                                      wrap=tk.WORD)
        self._txt_resultado.pack(fill=tk.BOTH, expand=True)

    def _generar_tabla(self):
        try:
            n = int(self._spin_vars.get())
            m = int(self._spin_rest.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa numeros validos.")
            return

        self._n_vars = n
        self._n_rest = m

        for widget in self._frame_tabla.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(self._frame_tabla, bg=COLOR_FRAME,
                           highlightthickness=0)
        scrollbar_v = ttk.Scrollbar(self._frame_tabla, orient="vertical",
                                    command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(self._frame_tabla, orient="horizontal",
                                    command=canvas.xview)
        canvas.configure(yscrollcommand=scrollbar_v.set,
                         xscrollcommand=scrollbar_h.set)
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame_inner = tk.Frame(canvas, bg=COLOR_FRAME)
        canvas.create_window((0, 0), window=frame_inner, anchor="nw")
        frame_inner.bind("<Configure>",
                         lambda e: canvas.configure(
                             scrollregion=canvas.bbox("all")))

        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []
        self._entries_nombres_rest = []

        col_offset = 2

        for j in range(n):
            e = tk.Entry(frame_inner, width=11, font=FONT_BOLD,
                         justify="center", relief="solid", bd=1, fg="#1a56db")
            e.insert(0, f"x{j+1}")
            e.grid(row=0, column=col_offset + j, padx=2, pady=2)
            self._entries_nombres_vars.append(e)

        tk.Label(frame_inner, text="b", font=FONT_BOLD,
                 bg=COLOR_FRAME, fg="#555").grid(
            row=0, column=col_offset + n, padx=6)
        tk.Label(frame_inner, text="Tipo", font=FONT_BOLD,
                 bg=COLOR_FRAME, fg="#555").grid(
            row=0, column=col_offset + n + 1, padx=4)

        tk.Label(frame_inner, text="Max Z", font=FONT_BOLD,
                 bg=COLOR_FRAME, fg="#c0392b").grid(
            row=1, column=0, padx=4, sticky="w")
        tk.Label(frame_inner, text="(F. Objetivo)", font=FONT_NORMAL,
                 bg=COLOR_FRAME, fg="#888").grid(row=1, column=1, padx=2)

        for j in range(n):
            e = tk.Entry(frame_inner, width=11, font=FONT_NORMAL,
                         justify="center", relief="solid", bd=1)
            e.insert(0, "0")
            e.grid(row=1, column=col_offset + j, padx=2, pady=2)
            self._entries_c.append(e)

        for i in range(m):
            tk.Label(frame_inner, text=f"R{i+1}", font=FONT_BOLD,
                     bg=COLOR_FRAME, fg="#555").grid(
                row=i+2, column=0, padx=4, sticky="w")

            e_nombre = tk.Entry(frame_inner, width=14, font=FONT_NORMAL,
                                relief="solid", bd=1, fg="#555")
            e_nombre.insert(0, f"Restriccion {i+1}")
            e_nombre.grid(row=i+2, column=1, padx=2, pady=2)
            self._entries_nombres_rest.append(e_nombre)

        self._tabla_A = TablaCoeficientes(frame_inner, m, n)
        self._tabla_A.grid(row=2, column=col_offset,
                           rowspan=m, columnspan=n, padx=0, pady=0)

        for i in range(m):
            e_b = tk.Entry(frame_inner, width=11, font=FONT_NORMAL,
                           justify="center", relief="solid", bd=1)
            e_b.insert(0, "0")
            e_b.grid(row=i+2, column=col_offset + n, padx=6, pady=2)
            self._entries_b.append(e_b)

            combo = ttk.Combobox(frame_inner, values=["<=", ">="],
                                 width=4, font=FONT_NORMAL, state="readonly")
            combo.set("<=")
            combo.grid(row=i+2, column=col_offset + n + 1, padx=4, pady=2)
            self._combos_tipo.append(combo)

    def _resolver(self):
        if self._tabla_A is None:
            messagebox.showwarning("Aviso", "Primero genera la tabla de datos.")
            return
        try:
            c     = [float(e.get()) for e in self._entries_c]
            b     = [float(e.get()) for e in self._entries_b]
            tipos = [cb.get() for cb in self._combos_tipo]
            A     = self._tabla_A.get_matriz()
            nombres_vars = [e.get() for e in self._entries_nombres_vars]
        except ValueError as err:
            messagebox.showerror("Error de entrada", str(err))
            return

        resultado = simplex_maximizacion(c, A, b, tipos)
        self._mostrar_resultado(resultado, nombres_vars)

    def _mostrar_resultado(self, res, nombres_vars):
        self._txt_resultado.config(state=tk.NORMAL, bg=COLOR_RESULTADO)
        self._txt_resultado.delete("1.0", tk.END)
        lineas = []

        if res['estado'] == 'optimo':
            lineas.append("SOLUCION OPTIMA ENCONTRADA")
            lineas.append("=" * 40)
            lineas.append(f"Iteraciones: {res['iteraciones']}")
            lineas.append("")
            for nombre, valor in zip(nombres_vars, res['x']):
                lineas.append(f"  {nombre:<18} = {valor:.6f}")
            lineas.append("")
            lineas.append(f"Valor maximo (Z) = {res['z']:,.4f}")
        else:
            self._txt_resultado.config(bg=COLOR_ERROR)
            lineas.append(res['estado'].upper().replace("_", " "))
            lineas.append("=" * 40)
            lineas.append(res['mensaje'])

        self._txt_resultado.insert(tk.END, "\n".join(lineas))
        self._txt_resultado.config(state=tk.DISABLED)


# ─────────────────────────────────────────
#  PESTANA: DUALIDAD
# ─────────────────────────────────────────

class PestanaDualidad(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_FONDO)
        self._tabla_A = None
        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []
        self._construir_ui()

    def _construir_ui(self):
        # ── Panel izquierdo ───────────────────────────────────────────────
        frame_config = tk.Frame(self, bg=COLOR_FONDO)
        frame_config.pack(side=tk.LEFT, fill=tk.Y, padx=PAD, pady=PAD)

        tk.Label(frame_config, text="Dualidad",
                 font=FONT_TITULO, bg=COLOR_FONDO).pack(anchor="w")
        tk.Label(frame_config, text="Conversion Primal -> Dual",
                 font=FONT_NORMAL, bg=COLOR_FONDO, fg="#666").pack(
            anchor="w", pady=(0, 10))

        # Tipo de primal
        frame_tipo = tk.LabelFrame(frame_config, text="Tipo de primal",
                                   font=FONT_BOLD, bg=COLOR_FRAME,
                                   padx=8, pady=6)
        frame_tipo.pack(fill=tk.X, pady=(0, 8))

        self._var_tipo = tk.StringVar(value="min")
        tk.Radiobutton(frame_tipo, text="Minimizacion", variable=self._var_tipo,
                       value="min", font=FONT_NORMAL, bg=COLOR_FRAME).pack(
            anchor="w")
        tk.Radiobutton(frame_tipo, text="Maximizacion", variable=self._var_tipo,
                       value="max", font=FONT_NORMAL, bg=COLOR_FRAME).pack(
            anchor="w")

        # Dimensiones
        frame_dim = tk.LabelFrame(frame_config, text="Dimensiones",
                                  font=FONT_BOLD, bg=COLOR_FRAME,
                                  padx=8, pady=6)
        frame_dim.pack(fill=tk.X, pady=(0, 8))

        tk.Label(frame_dim, text="Variables:", font=FONT_NORMAL,
                 bg=COLOR_FRAME).grid(row=0, column=0, sticky="w", pady=2)
        self._spin_vars = tk.Spinbox(frame_dim, from_=1, to=20, width=5,
                                     font=FONT_NORMAL)
        self._spin_vars.delete(0, tk.END)
        self._spin_vars.insert(0, "2")
        self._spin_vars.grid(row=0, column=1, padx=6, pady=2)

        tk.Label(frame_dim, text="Restricciones:", font=FONT_NORMAL,
                 bg=COLOR_FRAME).grid(row=1, column=0, sticky="w", pady=2)
        self._spin_rest = tk.Spinbox(frame_dim, from_=1, to=20, width=5,
                                     font=FONT_NORMAL)
        self._spin_rest.delete(0, tk.END)
        self._spin_rest.insert(0, "2")
        self._spin_rest.grid(row=1, column=1, padx=6, pady=2)

        tk.Button(frame_dim, text="Generar tabla",
                  font=FONT_BOLD, bg=COLOR_BTN, fg=COLOR_BTN_TEXT,
                  relief="flat", padx=8, pady=4,
                  command=self._generar_tabla).grid(
            row=2, column=0, columnspan=2, pady=(8, 2))

        tk.Button(frame_config, text="⇄  Convertir al Dual",
                  font=FONT_BOLD, bg="#7c3aed", fg=COLOR_BTN_TEXT,
                  relief="flat", padx=10, pady=6,
                  command=self._convertir).pack(fill=tk.X, pady=(4, 0))

        # ── Panel derecho ─────────────────────────────────────────────────
        frame_derecho = tk.Frame(self, bg=COLOR_FONDO)
        frame_derecho.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                           padx=(0, PAD), pady=PAD)

        self._frame_tabla = tk.LabelFrame(frame_derecho, text="Primal (datos de entrada)",
                                          font=FONT_BOLD, bg=COLOR_FRAME,
                                          padx=8, pady=6, height=320)
        self._frame_tabla.pack_propagate(False)
        self._frame_tabla.pack(fill=tk.X, expand=False)

        tk.Label(self._frame_tabla,
                 text="Presiona 'Generar tabla' para ingresar los datos.",
                 font=FONT_NORMAL, bg=COLOR_FRAME, fg="#888").pack(pady=20)

        self._frame_resultado = tk.LabelFrame(frame_derecho, text="Dual (resultado)",
                                              font=FONT_BOLD, bg=COLOR_RESULTADO,
                                              padx=8, pady=6)
        self._frame_resultado.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        self._txt_resultado = tk.Text(self._frame_resultado, height=12,
                                      font=FONT_MONO, bg=COLOR_RESULTADO,
                                      relief="flat", state=tk.DISABLED,
                                      wrap=tk.WORD)
        self._txt_resultado.pack(fill=tk.BOTH, expand=True)

    def _generar_tabla(self):
        try:
            n = int(self._spin_vars.get())
            m = int(self._spin_rest.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa numeros validos.")
            return

        for widget in self._frame_tabla.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(self._frame_tabla, bg=COLOR_FRAME,
                           highlightthickness=0)
        scrollbar_v = ttk.Scrollbar(self._frame_tabla, orient="vertical",
                                    command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(self._frame_tabla, orient="horizontal",
                                    command=canvas.xview)
        canvas.configure(yscrollcommand=scrollbar_v.set,
                         xscrollcommand=scrollbar_h.set)
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame_inner = tk.Frame(canvas, bg=COLOR_FRAME)
        canvas.create_window((0, 0), window=frame_inner, anchor="nw")
        frame_inner.bind("<Configure>",
                         lambda e: canvas.configure(
                             scrollregion=canvas.bbox("all")))

        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []

        col_offset = 1

        for j in range(n):
            e = tk.Entry(frame_inner, width=11, font=FONT_BOLD,
                         justify="center", relief="solid", bd=1, fg="#1a56db")
            e.insert(0, f"x{j+1}")
            e.grid(row=0, column=col_offset + j, padx=2, pady=2)
            self._entries_nombres_vars.append(e)

        tk.Label(frame_inner, text="b", font=FONT_BOLD,
                 bg=COLOR_FRAME, fg="#555").grid(
            row=0, column=col_offset + n, padx=6)
        tk.Label(frame_inner, text="Tipo", font=FONT_BOLD,
                 bg=COLOR_FRAME, fg="#555").grid(
            row=0, column=col_offset + n + 1, padx=4)

        tk.Label(frame_inner, text="Z", font=FONT_BOLD,
                 bg=COLOR_FRAME, fg="#7c3aed").grid(
            row=1, column=0, padx=4, sticky="w")

        for j in range(n):
            e = tk.Entry(frame_inner, width=11, font=FONT_NORMAL,
                         justify="center", relief="solid", bd=1)
            e.insert(0, "0")
            e.grid(row=1, column=col_offset + j, padx=2, pady=2)
            self._entries_c.append(e)

        self._tabla_A = TablaCoeficientes(frame_inner, m, n)
        self._tabla_A.grid(row=2, column=col_offset,
                           rowspan=m, columnspan=n, padx=0, pady=0)

        tipo_defecto = ">=" if self._var_tipo.get() == "min" else "<="

        for i in range(m):
            tk.Label(frame_inner, text=f"R{i+1}", font=FONT_BOLD,
                     bg=COLOR_FRAME, fg="#555").grid(
                row=i+2, column=0, padx=4, sticky="w")

            e_b = tk.Entry(frame_inner, width=11, font=FONT_NORMAL,
                           justify="center", relief="solid", bd=1)
            e_b.insert(0, "0")
            e_b.grid(row=i+2, column=col_offset + n, padx=6, pady=2)
            self._entries_b.append(e_b)

            combo = ttk.Combobox(frame_inner, values=["<=", ">="],
                                 width=4, font=FONT_NORMAL, state="readonly")
            combo.set(tipo_defecto)
            combo.grid(row=i+2, column=col_offset + n + 1, padx=4, pady=2)
            self._combos_tipo.append(combo)

    def _convertir(self):
        if self._tabla_A is None:
            messagebox.showwarning("Aviso", "Primero genera la tabla de datos.")
            return
        try:
            c     = [float(e.get()) for e in self._entries_c]
            b     = [float(e.get()) for e in self._entries_b]
            tipos = [cb.get() for cb in self._combos_tipo]
            A     = self._tabla_A.get_matriz()
            nombres_vars = [e.get() for e in self._entries_nombres_vars]
        except ValueError as err:
            messagebox.showerror("Error de entrada", str(err))
            return

        tipo_primal = self._var_tipo.get()
        dual = convertir_dual(tipo_primal, c, A, b, tipos, nombres_vars)

        self._txt_resultado.config(state=tk.NORMAL, bg=COLOR_RESULTADO)
        self._txt_resultado.delete("1.0", tk.END)

        if dual['error']:
            self._txt_resultado.config(bg=COLOR_ERROR)
            self._txt_resultado.insert(tk.END, f"Error: {dual['error']}")
        else:
            texto = formatear_dual(dual)
            self._txt_resultado.insert(tk.END, texto)

        self._txt_resultado.config(state=tk.DISABLED)


# ─────────────────────────────────────────
#  VENTANA PRINCIPAL
# ─────────────────────────────────────────

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Metodo Simplex")
        self.configure(bg=COLOR_FONDO)
        self.state("zoomed")

        # Estilo de pestanas
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
        style.configure("TNotebook.Tab", font=FONT_BOLD, padding=(16, 6))
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_BTN), ("!selected", "#dde3ea")],
                  foreground=[("selected", "white"),   ("!selected", "#333")])

        # Notebook (pestanas)
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tab_min = PestanaMinimizacion(notebook)
        tab_max = PestanaMaximizacion(notebook)
        tab_dual = PestanaDualidad(notebook)

        notebook.add(tab_min,  text="  Minimizacion  ")
        notebook.add(tab_max,  text="  Maximizacion  ")
        notebook.add(tab_dual, text="  Dualidad  ")


# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────

if __name__ == '__main__':
    app = App()
    app.mainloop()
