# Modos de Conducción - DriveLink2

## Descripción

Los modos de conducción permiten diferentes formas de procesar las entradas del volante y pedales antes de enviarlas a los sistemas de salida.

## Modos Disponibles

### 1. Modo Directo (`direct`)

**Descripción:** Modo de paso directo sin procesamiento. Las entradas del volante y pedales se envían directamente a la salida sin ninguna modificación o simulación.

**Características:**
- Sin procesamiento adicional
- Latencia mínima
- Ideal para aplicaciones que requieren control directo
- No simula marchas ni física del vehículo

**Uso:**
```bash
python main.py -m direct
```

**Telemetría:**
- Potencia: Basada en el acelerador
- Velocidad: Valor aproximado del acelerador
- Marcha: Siempre en neutral (N)
- RPM: Valor aproximado del acelerador

---

### 2. Modo carsim (`carsim`)

**Descripción:** Simula un coche real con transmisión manual, física de motor, y cambio de marchas.

**Características:**
- Simulación de transmisión manual de 6 velocidades + reversa
- Física realista del motor (RPM, aceleración)
- Sistema de embrague
- Cálculo de velocidad basado en la marcha y RPM
- Ratios de marchas configurados para realismo

**Controles:**
- **Acelerador:** Control de potencia del motor
- **Freno:** Desaceleración
- **Embrague:** Control del acoplamiento motor-transmisión
- **Shift Up (botón):** Cambiar a marcha superior
- **Shift Down (botón):** Cambiar a marcha inferior

**Marchas:**
- R: Reversa (ratio: -3.5)
- N: Neutral (ratio: 0.0)
- 1: Primera (ratio: 3.8)
- 2: Segunda (ratio: 2.5)
- 3: Tercera (ratio: 1.8)
- 4: Cuarta (ratio: 1.3)
- 5: Quinta (ratio: 1.0)
- 6: Sexta (ratio: 0.8)

**Parámetros de Motor:**
- RPM máximas: 8000
- RPM en ralentí: 1000
- Línea roja: 7500 RPM
- Ratio final de transmisión: 3.5

**Uso:**
```bash
python main.py -m carsim
```

**Telemetría:**
- Potencia: % de acelerador aplicado
- Velocidad: Calculada según marcha, RPM y física
- Marcha: Marcha actual (R, N, 1-6)
- RPM: Revoluciones del motor por minuto

---

## Arquitectura

### Clase Base: `BaseDrivingMode`

Todos los modos heredan de esta clase base que define:

- `process_input(input_data)`: Procesa las entradas y devuelve datos de salida
- `update(delta_time)`: Actualiza la física y estado del modo
- `get_telemetry()`: Devuelve datos de telemetría para visualización
- `activate()` / `deactivate()`: Gestión del ciclo de vida del modo
- `reset()`: Reinicia el estado del modo

### Implementación de Nuevos Modos

Para crear un nuevo modo de conducción:

1. Crear archivo en `driving_modes/`
2. Heredar de `BaseDrivingMode`
3. Implementar métodos abstractos:
   - `process_input()`
   - `update()`
4. Registrar en `driving_modes/__init__.py`
5. Agregar opción en `main.py`

**Ejemplo:**
```python
from .base_mode import BaseDrivingMode

class MyMode(BaseDrivingMode):
    def __init__(self):
        super().__init__(name="MyMode", description="Mi modo personalizado")
    
    def process_input(self, input_data):
        # Procesar entradas
        return output_data
    
    def update(self, delta_time):
        # Actualizar física
        pass
```

---

## Interfaz Gráfica

La nueva interfaz incluye:

### Panel Central (abajo)
- **Tacómetro Izquierdo:** Potencia (0-100%)
- **Tacómetro Derecho:** Velocidad (0-300 km/h)
- **Indicador Central:** Marcha activa (R, N, 1-6)
- **Barra RPM:** Revoluciones del motor (0-8000)

### Panel Izquierdo (abajo)
- **Indicador de Posición:** Visualización del ángulo del volante
- **Inclinación:** Preparado para datos futuros de inclinación

### Panel Derecho (abajo)
- **Panel de Mensajes:**
  - Drivers utilizados
  - Errores y advertencias
  - Modo de conducción activo
  - Eventos del sistema

---

## Ejemplos de Uso

### Modo Directo con Serial Output
```bash
python main.py -m direct input default_input.json output serial
```

### Modo carsim con HTTP Output
```bash
python main.py -m carsim input default_input.json output http
```

### Modo carsim sin Output (solo visualización)
```bash
python main.py -m carsim input default_input.json
```

---

## Desarrollo Futuro

Posibles mejoras:
- Modo "Arcade" con física simplificada
- Modo "Drift" con física de derrape
- Soporte para transmisión automática
- Sistema de daño y desgaste
- Múltiples perfiles de vehículo
- Telemetría avanzada (temperatura, presión, etc.)
