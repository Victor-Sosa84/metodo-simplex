# Método Simplex — IO1, Semestre 1 - 2026, FICCT - UAGRM 

Aplicación de escritorio para resolver problemas de Programación Lineal usando el **Método Simplex**. Cuenta con una interfaz gráfica con tres pestañas: Minimización, Maximización y Dualidad.

## Descripción general

- **Minimización**: resuelve problemas de mínimo con restricciones `<=`, `>=` y `=` usando el método Gran M. Incluye el problema de raciones para vacas lecheras como ejemplo precargado.
- **Maximización**: resuelve problemas de máximo con restricciones `<=` y `>=` usando el Simplex estándar.
- **Dualidad**: convierte cualquier problema primal (MIN o MAX) a su dual y muestra la formulación resultante.

## Estructura de archivos

```
metodo-simplex/
├── main.py            # Punto de entrada
├── gui.py             # Interfaz gráfica (tkinter, 3 pestañas)
├── minimizacion.py    # Lógica del Simplex Gran M para minimización
├── maximizacion.py    # Lógica del Simplex estándar para maximización
└── dualidad.py        # Conversión primal → dual
```

## Requisitos

- Python 3.8 o superior
- [NumPy](https://numpy.org/)
- tkinter (incluido en la instalación estándar de Python)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Victor-Sosa84/metodo-simplex.git
cd metodo-simplex

# Instalar dependencias
pip install numpy
```

## Cómo correr el programa

```bash
python main.py
```

Se abrirá la ventana principal. Selecciona la pestaña deseada, define las dimensiones del problema, ingresa los coeficientes y presiona **Resolver** (o **Convertir al Dual** en la pestaña de Dualidad).
