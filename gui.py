"""
gui.py
------
Interfaz grafica del programa Metodo Simplex.
Dos pestanas: Simplex (Min/Max) | Dualidad

Proyecto: Metodo Simplex — IO1, Semestre 1 - 2026, FICCT - UAGRM
"""

import tkinter as tk
from tkinter import ttk, messagebox

from minimizacion import simplex_gran_m, simplex_gran_m_pasos
from dualidad import convertir_dual, formatear_dual

try:
    from maximizacion import simplex_maximizacion, simplex_maximizacion_pasos
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

COLOR_FONDO     = "#f4f4f4"
COLOR_FRAME     = "#ffffff"
COLOR_BTN       = "#2c7be5"
COLOR_BTN_TEXT  = "#ffffff"
COLOR_RESULTADO = "#f0f7ff"
COLOR_ERROR     = "#fff0f0"

PAD = 14


# ─────────────────────────────────────────
#  WIDGET REUTILIZABLE: Tabla de coeficientes
# ─────────────────────────────────────────

class TablaCoeficientes(tk.Frame):

    def __init__(self, parent, filas, columnas, **kwargs):
        super().__init__(parent, bg=COLOR_FRAME, **kwargs)
        self.filas = filas
        self.columnas = columnas
        self.celdas = []

        for i in range(filas):
            fila_celdas = []
            for j in range(columnas):
                entry = tk.Entry(self, width=11, font=FONT_NORMAL,
                                 justify="center", relief="solid", bd=1)
                entry.insert(0, "0")
                entry.grid(row=i, column=j, padx=2, pady=2)
                fila_celdas.append(entry)
            self.celdas.append(fila_celdas)

    def get_matriz(self):
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
#  PESTANA: SIMPLEX (Min / Max)
# ─────────────────────────────────────────

class PestanaSimplex(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_FONDO)
        self._tabla_A = None
        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []
        self._entries_nombres_rest = []
        self._construir_ui()

    def _construir_ui(self):
        # ── Panel izquierdo ───────────────────────────────────────────────
        frame_config = tk.Frame(self, bg=COLOR_FONDO)
        frame_config.pack(side=tk.LEFT, fill=tk.Y, padx=PAD, pady=PAD)

        tk.Label(frame_config, text="Metodo Simplex",
                 font=FONT_TITULO, bg=COLOR_FONDO).pack(anchor="w")

        # Dropdown Min / Max
        frame_tipo = tk.LabelFrame(frame_config, text="Tipo de problema",
                                   font=FONT_BOLD, bg=COLOR_FRAME,
                                   padx=8, pady=6)
        frame_tipo.pack(fill=tk.X, pady=(8, 8))

        self._var_tipo = tk.StringVar(value="Minimizar")
        combo_tipo = ttk.Combobox(frame_tipo,
                                  textvariable=self._var_tipo,
                                  values=["Minimizar", "Maximizar"],
                                  font=FONT_BOLD, state="readonly", width=12)
        combo_tipo.pack(fill=tk.X)
        combo_tipo.bind("<<ComboboxSelected>>", self._on_tipo_cambio)

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

        # Boton ejemplo vacas (solo visible en Min)
        self._btn_vacas = tk.Button(frame_config,
                                    text="Cargar ejemplo: Vacas Lecheras",
                                    font=FONT_NORMAL, bg="#e8f0fe", fg="#1a56db",
                                    relief="flat", padx=6, pady=3,
                                    command=self._cargar_vacas)
        self._btn_vacas.pack(fill=tk.X, pady=(0, 6))

        tk.Button(frame_config, text="▶  Resolver",
                  font=FONT_BOLD, bg="#1a7f37", fg=COLOR_BTN_TEXT,
                  relief="flat", padx=10, pady=6,
                  command=self._resolver).pack(fill=tk.X, pady=(4, 0))

        # ── Panel derecho ─────────────────────────────────────────────────
        frame_derecho = tk.Frame(self, bg=COLOR_FONDO)
        frame_derecho.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                           padx=(0, PAD), pady=PAD)

        # Fila superior: datos + modelo estandarizado (grid para control de ancho)
        frame_superior = tk.Frame(frame_derecho, bg=COLOR_FONDO)
        frame_superior.pack(fill=tk.X, expand=False)
        frame_superior.columnconfigure(0, weight=2)
        frame_superior.columnconfigure(1, weight=1)

        self._frame_tabla = tk.LabelFrame(frame_superior, text="Datos del problema",
                                          font=FONT_BOLD, bg=COLOR_FRAME,
                                          padx=8, pady=6, height=320)
        self._frame_tabla.pack_propagate(False)
        self._frame_tabla.grid(row=0, column=0, sticky="nsew")

        tk.Label(self._frame_tabla,
                 text="Selecciona el tipo de problema y presiona 'Generar tabla'.",
                 font=FONT_NORMAL, bg=COLOR_FRAME, fg="#888").pack(pady=20)

        frame_modelo = tk.LabelFrame(frame_superior, text="Modelo estandarizado",
                                     font=FONT_BOLD, bg=COLOR_FRAME,
                                     padx=8, pady=6, height=320)
        frame_modelo.pack_propagate(False)
        frame_modelo.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self._txt_modelo = tk.Text(frame_modelo, font=FONT_MONO,
                                   bg=COLOR_FRAME, relief="flat",
                                   state=tk.DISABLED, wrap=tk.NONE)
        self._txt_modelo.pack(fill=tk.BOTH, expand=True)

        # ── Fila inferior: Resultado (izq) + Tablas Simplex (der) ─────────
        frame_inferior = tk.Frame(frame_derecho, bg=COLOR_FONDO)
        frame_inferior.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        self._frame_resultado = tk.LabelFrame(frame_inferior, text="Resultado",
                                              font=FONT_BOLD, bg=COLOR_RESULTADO,
                                              padx=8, pady=6)
        self._frame_resultado.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._txt_resultado = tk.Text(self._frame_resultado, width=38,
                                      font=FONT_MONO, bg=COLOR_RESULTADO,
                                      relief="flat", state=tk.DISABLED,
                                      wrap=tk.WORD)
        self._txt_resultado.pack(fill=tk.BOTH, expand=True)

        # Panel tablas Simplex
        frame_tablas = tk.LabelFrame(frame_inferior, text="Tablas Simplex (iteraciones)",
                                     font=FONT_BOLD, bg=COLOR_FRAME, padx=4, pady=4)
        frame_tablas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        self._tree = ttk.Treeview(frame_tablas, show="headings", selectmode="none")
        sv_tree = ttk.Scrollbar(frame_tablas, orient="vertical", command=self._tree.yview)
        sh_tree = ttk.Scrollbar(frame_tablas, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=sv_tree.set, xscrollcommand=sh_tree.set)
        sv_tree.pack(side=tk.RIGHT, fill=tk.Y)
        sh_tree.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(fill=tk.BOTH, expand=True)


    def _on_tipo_cambio(self, event=None):
        """Cuando cambia Min/Max: muestra u oculta el botón de vacas."""
        if self._var_tipo.get() == "Minimizar":
            self._btn_vacas.pack(fill=tk.X, pady=(0, 6),
                                 before=self._btn_vacas.master.winfo_children()[-1])
        else:
            self._btn_vacas.pack_forget()

        # Si ya hay tabla generada, actualizar label Z y tipos por defecto
        if self._tabla_A is not None:
            self._actualizar_label_z()
            self._actualizar_tipos_defecto()

    def _actualizar_label_z(self):
        """Actualiza el label Min Z / Max Z en la tabla sin regenerarla."""
        tipo = self._var_tipo.get()
        texto = "Min Z" if tipo == "Minimizar" else "Max Z"
        color = "#1a7f37" if tipo == "Minimizar" else "#c0392b"
        # Buscar el label en frame_inner y actualizarlo
        canvas = None
        for w in self._frame_tabla.winfo_children():
            if isinstance(w, tk.Canvas):
                canvas = w
                break
        if canvas:
            for item in canvas.winfo_children():
                for child in item.winfo_children():
                    if isinstance(child, tk.Label) and child.cget("text") in ("Min Z", "Max Z"):
                        child.config(text=texto, fg=color)

    def _actualizar_tipos_defecto(self):
        """Cambia el tipo por defecto de los combos al cambiar Min/Max."""
        tipo = self._var_tipo.get()
        defecto = ">=" if tipo == "Minimizar" else "<="
        for combo in self._combos_tipo:
            combo.set(defecto)

    def _generar_tabla(self):
        try:
            n = int(self._spin_vars.get())
            m = int(self._spin_rest.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa numeros validos.")
            return
        if n < 1 or m < 1:
            messagebox.showerror("Error", "Debe haber al menos 1 variable y 1 restriccion.")
            return

        for widget in self._frame_tabla.winfo_children():
            widget.destroy()

        tipo = self._var_tipo.get()
        es_min = tipo == "Minimizar"

        canvas = tk.Canvas(self._frame_tabla, bg=COLOR_FRAME, highlightthickness=0)
        sv = ttk.Scrollbar(self._frame_tabla, orient="vertical", command=canvas.yview)
        sh = ttk.Scrollbar(self._frame_tabla, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=sv.set, xscrollcommand=sh.set)
        sv.pack(side=tk.RIGHT, fill=tk.Y)
        sh.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        fi = tk.Frame(canvas, bg=COLOR_FRAME)
        canvas.create_window((0, 0), window=fi, anchor="nw")
        fi.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []
        self._entries_nombres_rest = []

        col_offset = 2

        # Fila 0: nombres de variables
        tk.Label(fi, text="", bg=COLOR_FRAME).grid(row=0, column=0, columnspan=2)
        for j in range(n):
            e = tk.Entry(fi, width=11, font=FONT_BOLD, justify="center",
                         relief="solid", bd=1, fg="#1a56db")
            e.insert(0, f"x{j+1}")
            e.grid(row=0, column=col_offset + j, padx=2, pady=2)
            self._entries_nombres_vars.append(e)

        tk.Label(fi, text="Tipo", font=FONT_BOLD, bg=COLOR_FRAME,
                 fg="#555").grid(row=0, column=col_offset + n, padx=4)
        tk.Label(fi, text="b", font=FONT_BOLD, bg=COLOR_FRAME,
                 fg="#555").grid(row=0, column=col_offset + n + 1, padx=6)

        # Fila 1: función objetivo
        label_z = "Min Z" if es_min else "Max Z"
        color_z = "#1a7f37" if es_min else "#c0392b"
        tk.Label(fi, text=label_z, font=FONT_BOLD, bg=COLOR_FRAME,
                 fg=color_z).grid(row=1, column=0, padx=4, sticky="w")
        tk.Label(fi, text="(F. Objetivo)", font=FONT_NORMAL, bg=COLOR_FRAME,
                 fg="#888").grid(row=1, column=1, padx=2)

        for j in range(n):
            e = tk.Entry(fi, width=11, font=FONT_NORMAL, justify="center",
                         relief="solid", bd=1)
            e.insert(0, "0")
            e.grid(row=1, column=col_offset + j, padx=2, pady=2)
            self._entries_c.append(e)

        # Filas de restricciones
        self._tabla_A = TablaCoeficientes(fi, m, n)
        self._tabla_A.grid(row=2, column=col_offset, rowspan=m, columnspan=n)

        tipo_defecto = ">=" if es_min else "<="
        # Min permite =, Max solo <= y >=
        valores_tipo = ["<=", ">=", "="] if es_min else ["<=", ">="]

        for i in range(m):
            tk.Label(fi, text=f"R{i+1}", font=FONT_BOLD, bg=COLOR_FRAME,
                     fg="#555").grid(row=i+2, column=0, padx=4, sticky="w")

            e_nombre = tk.Entry(fi, width=14, font=FONT_NORMAL,
                                relief="solid", bd=1, fg="#555")
            e_nombre.insert(0, f"Restriccion {i+1}")
            e_nombre.grid(row=i+2, column=1, padx=2, pady=2)
            self._entries_nombres_rest.append(e_nombre)

            combo = ttk.Combobox(fi, values=valores_tipo, width=4,
                                 font=FONT_NORMAL, state="readonly")
            combo.set(tipo_defecto)
            combo.grid(row=i+2, column=col_offset + n, padx=4, pady=2)
            self._combos_tipo.append(combo)

            e_b = tk.Entry(fi, width=11, font=FONT_NORMAL, justify="center",
                           relief="solid", bd=1)
            e_b.insert(0, "0")
            e_b.grid(row=i+2, column=col_offset + n + 1, padx=6, pady=2)
            self._entries_b.append(e_b)

    def _cargar_vacas(self):
        self._var_tipo.set("Minimizar")
        self._spin_vars.delete(0, tk.END)
        self._spin_vars.insert(0, "6")
        self._spin_rest.delete(0, tk.END)
        self._spin_rest.insert(0, "5")
        self._generar_tabla()

        nombres_vars = ["Maiz", "Sorgo", "T.Soya", "Afrechillo", "Alfalfa", "Hna.Hueso"]
        c_vals = [2300, 2000, 3200, 1350, 1650, 4000]
        A_vals = [
            [1,    1,    1,    1,    1,    1   ],
            [90,   100,  440,  150,  180,  0   ],
            [3300, 3150, 3200, 2450, 2100, 0   ],
            [25,   28,   60,   110,  250,  0   ],
            [0.2,  0.4,  2.5,  1.2,  14,   300 ],
        ]
        b_vals = [1, 160, 2600, 180, 6]
        tipos  = ["=", ">=", ">=", ">=", ">="]
        nombres_rest = [
            "Balance masa", "Proteina >= 160", "Energia >= 2600",
            "Fibra >= 180", "Calcio >= 6",
        ]

        for j, (nv, cv) in enumerate(zip(nombres_vars, c_vals)):
            self._entries_nombres_vars[j].delete(0, tk.END)
            self._entries_nombres_vars[j].insert(0, nv)
            self._entries_c[j].delete(0, tk.END)
            self._entries_c[j].insert(0, str(cv))

        for i, (fila, bv, tipo, nr) in enumerate(zip(A_vals, b_vals, tipos, nombres_rest)):
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
            c            = [float(e.get()) for e in self._entries_c]
            b            = [float(e.get()) for e in self._entries_b]
            tipos        = [cb.get() for cb in self._combos_tipo]
            A            = self._tabla_A.get_matriz()
            nombres_vars = [e.get() for e in self._entries_nombres_vars]
            nombres_rest = [e.get() for e in self._entries_nombres_rest]
        except ValueError as err:
            messagebox.showerror("Error de entrada", str(err))
            return

        tipo = self._var_tipo.get()

        if tipo == "Minimizar":
            for i, bv in enumerate(b):
                if bv < 0:
                    messagebox.showerror(
                        "Error", f"El valor b de la restriccion {i+1} es negativo.\n"
                                 "Multiplica la restriccion por -1 e invierte el tipo.")
                    return
            resultado = simplex_gran_m_pasos(c, A, b, tipos)
            self._mostrar_resultado(resultado, c, nombres_vars, nombres_rest, tipos, b, es_min=True)

        else:  # Maximizar
            if not MAXIMIZACION_DISPONIBLE:
                messagebox.showerror(
                    "No disponible",
                    "maximizacion.py aun no esta en el proyecto.\n"
                    "Agrega el archivo y reinicia el programa.")
                return
            resultado = simplex_maximizacion_pasos(c, A, b, tipos)
            self._mostrar_resultado(resultado, c, nombres_vars, nombres_rest, tipos, b, es_min=False)

        self._mostrar_tablas(resultado.get('pasos', []))
        es_min = (tipo == "Minimizar")
        self._mostrar_modelo(c, A, b, tipos, nombres_vars, nombres_rest, es_min)

    def _mostrar_resultado(self, res, c, nombres_vars, nombres_rest, tipos, b, es_min):
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
            etiqueta = "Costo minimo" if es_min else "Valor maximo"
            lineas.append(f"{etiqueta} (Z) = {res['z']:,.4f}")

            A_arr = self._tabla_A.get_matriz()
            lineas.append("")
            lineas.append("Verificacion de restricciones:")
            for i, (nombre, tipo, bv) in enumerate(zip(nombres_rest, tipos, b)):
                val = sum(A_arr[i][j] * res['x'][j] for j in range(len(res['x'])))
                lineas.append(f"  {nombre}: {val:.4f} {tipo} {bv}  ✓")

            # Detectar infinitas soluciones: variable no basica con coef 0 en fila Z
            pasos = res.get('pasos', [])
            if pasos:
                ultimo = pasos[-1]
                mat = ultimo['matriz']
                base_labels = ultimo['base']
                fila_z = mat[-2] if 'M' in base_labels else mat[-1]
                n_vars = len(res['x'])
                vars_basicas = set(base_labels) - {'Z', 'M'}
                for j in range(n_vars):
                    nombre_var = f"x{j+1}"
                    if nombre_var not in vars_basicas and abs(fila_z[j]) < 1e-8:
                        lineas.append("")
                        lineas.append("⚠ SOLUCIONES MULTIPLES (INFINITAS)")
                        lineas.append("La solucion mostrada es optima, pero")
                        lineas.append("existen infinitas soluciones con el")
                        lineas.append(f"mismo valor de Z ({res['z']:,.4f}).")
                        break

        elif res['estado'] == 'no_factible':
            self._txt_resultado.config(bg=COLOR_ERROR)
            lineas.append("SIN SOLUCION FACTIBLE")
            lineas.append("=" * 40)
            lineas.append(res['mensaje'])
            lineas.append("")
            lineas.append("Posibles causas:")
            lineas.append("  - Restricciones contradictorias entre si.")
            lineas.append("  - No existe punto que satisfaga todas")
            lineas.append("    las restricciones simultaneamente.")
            lineas.append("")
            lineas.append("Sugerencia: revisa los signos y valores")
            lineas.append("de las restricciones.")

        elif res['estado'] == 'no_acotado':
            self._txt_resultado.config(bg=COLOR_ERROR)
            lineas.append("PROBLEMA NO ACOTADO")
            lineas.append("=" * 40)
            lineas.append(res['mensaje'])

        self._txt_resultado.insert(tk.END, "\n".join(lineas))
        self._txt_resultado.config(state=tk.DISABLED)

    def _mostrar_tablas(self, pasos):
        """Puebla el Treeview con todas las tablas de iteraciones."""
        self._tree.delete(*self._tree.get_children())
        if not pasos:
            return

        headers = pasos[0]['headers']
        cols = ["Base"] + headers
        self._tree["columns"] = cols

        self._tree.heading("Base", text="Base")
        self._tree.column("Base", width=110, anchor="center", stretch=False)
        for h in headers:
            self._tree.heading(h, text=h)
            ancho = 45 if h != "b" else 70
            self._tree.column(h, width=ancho, anchor="center", stretch=False)

        for paso in pasos:
            # Fila separadora con título
            self._tree.insert("", "end", values=[paso['titulo']] + [""] * len(headers),
                              tags=("titulo",))
            mat = paso['matriz']
            base = paso['base']
            for i, fila_base in enumerate(base):
                vals = [fila_base]
                for j in range(len(mat[i])):
                    v = mat[i, j]
                    vals.append("0" if abs(v) < 1e-9 else f"{v:.2f}")
                self._tree.insert("", "end", values=vals)
            # Fila en blanco entre iteraciones
            self._tree.insert("", "end", values=[""] * len(cols))

        self._tree.tag_configure("titulo", background="#dde3ea", font=FONT_BOLD)

    def _mostrar_modelo(self, c, A, b, tipos, nombres_vars, nombres_rest, es_min):
        tipo_str = "Min" if es_min else "Max"
        n = len(c)
        m = len(b)

        def fmt(v):
            return str(int(v)) if v == int(v) else str(v)

        # Paso 1: asignar holguras/excesos primero (igual que el algoritmo)
        col = n
        excesos = {}   # i -> col_idx
        holguras = {}  # i -> col_idx
        for i, tipo in enumerate(tipos):
            if tipo == '<=':
                holguras[i] = col; col += 1
            elif tipo == '>=':
                excesos[i] = col; col += 1

        # Paso 2: asignar artificiales después
        artificiales = {}  # i -> col_idx
        art_cols = set()
        for i, tipo in enumerate(tipos):
            if tipo in ('>=', '='):
                artificiales[i] = col
                art_cols.add(col)
                col += 1
        total = col

        lineas = []

        # Función objetivo
        terms_fo = [f"{fmt(c[j])}x{j+1}" for j in range(n)]
        for j in range(n, total):
            if j in art_cols:
                # MIN usa Gran M, MAX usa Dos Fases (sin M en f.obj.)
                terms_fo.append(f"Mx{j+1}" if es_min else f"0x{j+1}")
            else:
                terms_fo.append(f"0x{j+1}")
        lineas.append(f"{tipo_str} Z = " + " + ".join(terms_fo))
        lineas.append("")
        lineas.append("Restricciones:")

        for i in range(m):
            parts = [f"{fmt(A[i][j])}x{j+1}" for j in range(n)]
            if i in excesos:
                parts.append(f"- x{excesos[i]+1}")
            if i in holguras:
                parts.append(f"+ x{holguras[i]+1}")
            if i in artificiales:
                parts.append(f"+ x{artificiales[i]+1}")
            # Unir con + excepto los que ya tienen signo propio (- o +)
            linea = parts[0]
            for p in parts[1:]:
                if p.startswith(('+', '-')):
                    linea += f" {p}"
                else:
                    linea += f" + {p}"
            bv = fmt(b[i])
            lineas.append(f"  {linea} = {bv}")

        lineas.append("")
        all_vars = ", ".join([f"x{j+1}" for j in range(total)])
        lineas.append(f"  {all_vars} >= 0")

        self._txt_modelo.config(state=tk.NORMAL)
        self._txt_modelo.delete("1.0", tk.END)
        self._txt_modelo.insert(tk.END, "\n".join(lineas))
        self._txt_modelo.config(state=tk.DISABLED)


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
        frame_config = tk.Frame(self, bg=COLOR_FONDO)
        frame_config.pack(side=tk.LEFT, fill=tk.Y, padx=PAD, pady=PAD)

        tk.Label(frame_config, text="Dualidad",
                 font=FONT_TITULO, bg=COLOR_FONDO).pack(anchor="w")
        tk.Label(frame_config, text="Conversion Primal -> Dual",
                 font=FONT_NORMAL, bg=COLOR_FONDO, fg="#666").pack(anchor="w", pady=(0, 10))

        frame_tipo = tk.LabelFrame(frame_config, text="Tipo de primal",
                                   font=FONT_BOLD, bg=COLOR_FRAME, padx=8, pady=6)
        frame_tipo.pack(fill=tk.X, pady=(0, 8))

        self._var_tipo = tk.StringVar(value="min")
        ttk.Combobox(frame_tipo, textvariable=self._var_tipo,
                     values=["min", "max"],
                     font=FONT_BOLD, state="readonly", width=12).pack(fill=tk.X)

        frame_dim = tk.LabelFrame(frame_config, text="Dimensiones",
                                  font=FONT_BOLD, bg=COLOR_FRAME, padx=8, pady=6)
        frame_dim.pack(fill=tk.X, pady=(0, 8))

        tk.Label(frame_dim, text="Variables:", font=FONT_NORMAL,
                 bg=COLOR_FRAME).grid(row=0, column=0, sticky="w", pady=2)
        self._spin_vars = tk.Spinbox(frame_dim, from_=1, to=20, width=5, font=FONT_NORMAL)
        self._spin_vars.delete(0, tk.END)
        self._spin_vars.insert(0, "2")
        self._spin_vars.grid(row=0, column=1, padx=6, pady=2)

        tk.Label(frame_dim, text="Restricciones:", font=FONT_NORMAL,
                 bg=COLOR_FRAME).grid(row=1, column=0, sticky="w", pady=2)
        self._spin_rest = tk.Spinbox(frame_dim, from_=1, to=20, width=5, font=FONT_NORMAL)
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
                                      relief="flat", state=tk.DISABLED, wrap=tk.WORD)
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

        canvas = tk.Canvas(self._frame_tabla, bg=COLOR_FRAME, highlightthickness=0)
        sv = ttk.Scrollbar(self._frame_tabla, orient="vertical", command=canvas.yview)
        sh = ttk.Scrollbar(self._frame_tabla, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=sv.set, xscrollcommand=sh.set)
        sv.pack(side=tk.RIGHT, fill=tk.Y)
        sh.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        fi = tk.Frame(canvas, bg=COLOR_FRAME)
        canvas.create_window((0, 0), window=fi, anchor="nw")
        fi.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self._entries_c = []
        self._entries_b = []
        self._combos_tipo = []
        self._entries_nombres_vars = []

        col_offset = 1

        for j in range(n):
            e = tk.Entry(fi, width=11, font=FONT_BOLD, justify="center",
                         relief="solid", bd=1, fg="#1a56db")
            e.insert(0, f"x{j+1}")
            e.grid(row=0, column=col_offset + j, padx=2, pady=2)
            self._entries_nombres_vars.append(e)

        tk.Label(fi, text="Tipo", font=FONT_BOLD, bg=COLOR_FRAME,
                 fg="#555").grid(row=0, column=col_offset + n, padx=4)
        tk.Label(fi, text="b", font=FONT_BOLD, bg=COLOR_FRAME,
                 fg="#555").grid(row=0, column=col_offset + n + 1, padx=6)

        tk.Label(fi, text="Z", font=FONT_BOLD, bg=COLOR_FRAME,
                 fg="#7c3aed").grid(row=1, column=0, padx=4, sticky="w")

        for j in range(n):
            e = tk.Entry(fi, width=11, font=FONT_NORMAL, justify="center",
                         relief="solid", bd=1)
            e.insert(0, "0")
            e.grid(row=1, column=col_offset + j, padx=2, pady=2)
            self._entries_c.append(e)

        self._tabla_A = TablaCoeficientes(fi, m, n)
        self._tabla_A.grid(row=2, column=col_offset, rowspan=m, columnspan=n)

        tipo_defecto = ">=" if self._var_tipo.get() == "min" else "<="

        for i in range(m):
            tk.Label(fi, text=f"R{i+1}", font=FONT_BOLD, bg=COLOR_FRAME,
                     fg="#555").grid(row=i+2, column=0, padx=4, sticky="w")

            combo = ttk.Combobox(fi, values=["<=", ">="], width=4,
                                 font=FONT_NORMAL, state="readonly")
            combo.set(tipo_defecto)
            combo.grid(row=i+2, column=col_offset + n, padx=4, pady=2)
            self._combos_tipo.append(combo)

            e_b = tk.Entry(fi, width=11, font=FONT_NORMAL, justify="center",
                           relief="solid", bd=1)
            e_b.insert(0, "0")
            e_b.grid(row=i+2, column=col_offset + n + 1, padx=6, pady=2)
            self._entries_b.append(e_b)

    def _convertir(self):
        if self._tabla_A is None:
            messagebox.showwarning("Aviso", "Primero genera la tabla de datos.")
            return
        try:
            c            = [float(e.get()) for e in self._entries_c]
            b            = [float(e.get()) for e in self._entries_b]
            tipos        = [cb.get() for cb in self._combos_tipo]
            A            = self._tabla_A.get_matriz()
            nombres_vars = [e.get() for e in self._entries_nombres_vars]
        except ValueError as err:
            messagebox.showerror("Error de entrada", str(err))
            return

        dual = convertir_dual(self._var_tipo.get(), c, A, b, tipos, nombres_vars)

        self._txt_resultado.config(state=tk.NORMAL, bg=COLOR_RESULTADO)
        self._txt_resultado.delete("1.0", tk.END)

        if dual['error']:
            self._txt_resultado.config(bg=COLOR_ERROR)
            self._txt_resultado.insert(tk.END, f"Error: {dual['error']}")
        else:
            self._txt_resultado.insert(tk.END, formatear_dual(dual))

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

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
        style.configure("TNotebook.Tab", font=FONT_BOLD, padding=(16, 6))
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_BTN), ("!selected", "#dde3ea")],
                  foreground=[("selected", "white"),   ("!selected", "#333")])

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        notebook.add(PestanaSimplex(notebook),  text="  Simplex  ")
        notebook.add(PestanaDualidad(notebook), text="  Dualidad  ")


# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────

if __name__ == '__main__':
    app = App()
    app.mainloop()