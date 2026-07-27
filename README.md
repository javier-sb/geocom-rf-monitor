# GEOCOM RF Monitor

## Descripción

GEOCOM RF Monitor es una herramienta de monitoreo continuo diseñada para supervisar la presencia de la señal de radio de la estación base GNSS de GEOCOM utilizando un receptor RTL-SDR.

El sistema detecta automáticamente cambios en el estado de la transmisión (ONLINE/OFFLINE), registra eventos en un archivo de log y envía notificaciones mediante Telegram, permitiendo conocer el estado de la estación base.

---

# Hardware utilizado

| Componente | Descripción |
|------------|-------------|
| Raspberry Pi 4 Model B | Equipo encargado de ejecutar el servicio de monitoreo y gestionar las notificaciones. |
| RTL-SDR V4c | Receptor SDR utilizado para la adquisición de muestras IQ de la señal RF. |
| Filtro pasabanda RF 400–475 MHz (433 MHz) | Atenúa señales fuera de la banda de interés, mejorando la relación señal/ruido durante el monitoreo. |
| Base para antena con cable de extensión SMA macho-hembra | Permite una ubicación más conveniente de la antena |
| Adaptador SMA macho a TNC hembra (TNCK-SMAJ) | Adaptador utilizado para conectar la antena con conector TNC al sistema SDR. |
| Antena UHF (400–470 MHz) | Antena utilizada para la recepción de la transmisión de la estación base GNSS. |
| Red Ethernet/Wi-Fi | Proporciona conectividad a Internet para el envío de notificaciones mediante Telegram. |

## Esquema del sistema

```
           Antena UHF
                │
              TNC
                │
       Adaptador TNC → SMA
                │
  Base con cable SMA de extensión
                │
   Filtro pasabanda 400–475 MHz
                │
            RTL-SDR V4c
                │ USB
                │
         Raspberry Pi 4
                │
          Red Ethernet/Wi-Fi
                │
          API de Telegram
                │
  Grupo de monitoreo GEOCOM en Telegram
```

---

# Parámetros de monitoreo

| Parámetro | Valor |
|-----------|-------|
| Frecuencia | 454.975 MHz |
| Sample Rate | 250 kS/s |
| Muestras | 65536 |
| Ganancia | 30 dB |
| Umbral de detección | -37 dB |
| Timeout OFFLINE | 60 s |
| Intervalo de monitoreo | 0.2 s |

---

# Funcionamiento

El sistema realiza continuamente las siguientes operaciones:

1. Captura muestras IQ desde el RTL-SDR.
2. Calcula la potencia de la señal en ese momento de muestreo.
3. Convierte la potencia a una escala relativa en dB.
4. Compara la medición con el umbral configurado.
5. Determina el estado ONLINE/OFFLINE.
6. Registra cambios de estado.
7. Envía notificaciones mediante Telegram.

# Algoritmo

```text
Lectura de muestras IQ
        │
        ▼
Cálculo de potencia promedio
        │
        ▼
¿Potencia > Umbral?
        │
 ┌──────┴──────┐
 │             │
Sí             No
 │             │
Actualizar      Esperar
last_seen       siguiente lectura
 │
 ▼
¿Han pasado más de 60 segundos
sin detectar señal?
        │
 ┌──────┴──────┐
 │             │
No            Sí
 │             │
ONLINE      OFFLINE
```

---

# Telegram

## Notificaciones automáticas

- Inicio del monitor.
- Cambio a ONLINE.
- Cambio a OFFLINE.
- Reporte diario (08:00 hrs).

## Comandos 

### `/alive@geocomrf_bot`

Devuelve:

- Estado actual.
- Tiempo en el estado actual.
- Potencia relativa.
- Frecuencia monitoreada.
- Fecha y hora de consulta.

---

# Ejemplo de utilizacion

<img width="467" height="555" alt="image" src="https://github.com/user-attachments/assets/98729b72-50ca-4de6-899f-0649a009d97f" />
