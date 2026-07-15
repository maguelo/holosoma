# Plan: Benchmark estandarizado de políticas de locomoción

> **Estado:** propuesta para discutir · **Fecha:** 2026-07-16
> **Objetivo:** comparar checkpoints (exp_00X, y modelos upstream .onnx) con métricas
> reproducibles y un informe generado automáticamente.

---

## 1. Motivación

Hoy comparamos políticas viendo el viewer y anotando impresiones en TASKS.md
("strafe no es estable", "82% aéreo"). Necesitamos:

1. **Métricas cuantitativas** con definición fija, para que "mejor" signifique lo mismo
   en todos los experimentos.
2. **Escenarios deterministas** (semilla fija, N repeticiones) para que dos runs del
   mismo checkpoint den el mismo resultado.
3. **Informe comparativo** automático: tabla + gráfico por checkpoint.

Esto es el patrón estándar de la industria: *benchmark harness* = suite de escenarios
aislados (probes) + extractor de métricas + generador de informes. No es una
aplicación interactiva; es un pipeline batch que se corre contra cada checkpoint.

---

## 2. Qué tenemos ya (no partimos de cero)

| Pieza | Estado |
|---|---|
| `loop/eval_sequence.py` | Corre secuencias scripted de comandos (circuits `basic`, `football`) y graba `.npz` |
| `RecordingCallback` | Ya guarda por step: `root_pos`, `root_quat`, `root_lin_vel`, `root_ang_vel`, `dof_pos/vel`, `torques`, `actions`, `commanded_velocity`, `body_pos_w` (todos los cuerpos, incl. pies) |
| `EvalPushCallback` | **Ya aplica pulsos de fuerza al robot** y graba `push_force_w`, `push_active` — la base de push-recovery está hecha |
| `loop/extract_metrics.py` | Extrae métricas de *training* (TFEvents → JSON) — mismo patrón, distinta fuente |
| Soporte ONNX | `eval_sequence.py` ya evalúa `.onnx` (modelos upstream) además de `.pt` |
| Terrenos procedurales | El training ya genera terrenos randomizados reutilizables para el test de caídas |

**Conclusión:** la mayor parte del trabajo es *análisis de los npz* y *nuevos probes*,
no infraestructura nueva.

---

## 3. Arquitectura propuesta

```
loop/benchmark/
├── scenarios/              # definición de cada probe (comandos + config)
│   ├── ramp_vx.py          #   speed.forward/backward + deadzone + tracking
│   ├── ramp_vy.py          #   speed.strafing + deadzone
│   ├── ramp_vrz.py         #   speed.rotation + deadzone
│   ├── turn_180.py         #   agility.timetoturn
│   ├── gait_probe.py       #   stability.feet, floorcontactratio, stepsize, period
│   ├── push_recovery.py    #   robustness.push.{front,back,side}
│   └── terrain_falls.py    #   stability.falls
├── metrics.py              # npz → dict de métricas (funciones puras, testeables)
├── runner.py               # corre la suite completa → results/<checkpoint_id>.json
├── report.py               # N JSONs → informe MD (tabla + radar chart)
└── results/                # un JSON por checkpoint evaluado (versionado en git)
```

Principios:

- **Probes aislados, no circuitos**: cada métrica se mide en el escenario mínimo que
  la aísla. Los circuitos (basic/football) se mantienen como *test de integración*.
- **Separar captura de análisis**: los escenarios solo generan `.npz`; las métricas se
  calculan offline en `metrics.py`. Así podemos recalcular métricas sobre npz viejos
  sin re-simular.
- **JSON por checkpoint con esquema estable** (sección 5). Los resultados se
  versionan en git → historia de progreso gratis.
- **Determinismo**: semilla fija + N=3 repeticiones (media ± std en el informe).

Entrada única:

```bash
make benchmark CHECKPOINT=logs/.../model_80896.pt        # suite completa → JSON
make benchmark-report                                     # todos los JSON → informe
```

---

## 4. Catálogo de métricas

### 4.1 Velocidad y deadzone — probe: *ramp test* (Fase 1)

Un solo escenario por eje da cuatro métricas. Setpoint en escalones crecientes
(p. ej. 0.0 → 3.0 m/s en pasos de 0.1, 4 s por escalón, con los 1.5 s primeros
descartados como transitorio):

| Métrica | Definición |
|---|---|
| `speed.forward` | máx. vx real sostenida (media del escalón) antes de caída o divergencia |
| `speed.backward` | ídem con −vx |
| `speed.strafing` | ídem con ±vy (reportar ambos lados — sabemos que no es simétrico) |
| `speed.rotation` | ídem con ±vrz |
| `deadzone.*` | primer setpoint cuyo escalón alcanza >50 % del comando |
| `tracking.*.rmse` | RMSE (real − comando) en la zona lineal — **añadida**: es la métrica estándar #1 en locomoción y sale gratis del mismo run |
| `tracking.*.linear_range` | rango de comandos donde el error relativo <20 % (la "zona útil" de la política) |

*Por qué ramp y no búsqueda binaria:* un único run da la curva completa
comando-vs-real, de la que salen velocidad máxima, deadzone y tracking a la vez.

### 4.2 Marcha y contacto — probe: *gait probe* (Fase 2)

Secuencia fija de setpoints (0.5 / 1.0 / 1.5 / 2.0 m/s, 8 s cada uno), métricas por
setpoint. Contacto estimado de `body_pos_w` de los pies (altura + velocidad vertical
≈ 0), o mejor, ampliando el recorder para guardar fuerzas de contacto reales
(decisión abierta, sección 8).

| Métrica | Definición |
|---|---|
| `gait.contact_ratio` | fracción del ciclo con ≥1 pie en contacto (↓ mejor para correr; el 82 % aéreo de exp_006 saldría de aquí) |
| `gait.step_length` | distancia media entre huellas consecutivas del mismo pie |
| `gait.period` | periodo de ciclo (autocorrelación del patrón de contacto) |
| `stability.feet` | varianza de la duración de contacto entre pasos + tasa de doble rebote/arrastre (pie que toca-despega-toca en <100 ms) |
| `gait.symmetry` | ratio izq/der de step_length y duración de contacto (detectaría la asimetría del strafe que tenemos anotada) |

### 4.3 Agilidad — probe: *turn test* (Fase 1)

| Métrica | Definición |
|---|---|
| `agility.timetoturn.left/right` | comando de yaw 180°; tiempo hasta error de heading <10° sostenido 0.5 s |
| `agility.stop_distance` | de sprint 2.0 m/s a comando 0; distancia hasta ‖v‖ < 0.1 m/s |

### 4.4 Robustez — probe: *push recovery* (Fase 3)

En lugar de disparar pelotas físicas, aplicar **impulsos de fuerza al torso**
(estándar en la literatura de push-recovery y más reproducible: la pelota mete ruido
de rebote y punto de contacto). `EvalPushCallback` ya hace el 80 % de esto — falta
hacer el impulso determinista (dirección/magnitud fijas) en vez de aleatorio.

| Métrica | Definición |
|---|---|
| `robustness.push.front/back/side` | impulso máximo (N·s) que el robot sobrevive, iterando magnitud creciente. Medido de pie y a 1.0 m/s |

La pelota física queda como extensión futura (es mejor demo, no mejor métrica).

### 4.5 Caídas en terreno — probe: *terrain gauntlet* (Fase 4)

Reutiliza el generador de terrenos del training con dificultad por niveles.

| Métrica | Definición |
|---|---|
| `stability.falls.flat` | caídas por minuto en el gait probe (debería ser 0) |
| `stability.falls.terrain_level` | máximo nivel de dificultad con tasa de éxito ≥80 % (N episodios por nivel) |
| `stability.mean_distance_to_fall` | distancia media recorrida antes de caer en el nivel límite |

Definición de "caída" (única para todo el benchmark): altura del pelvis < 0.4 m
o inclinación del torso > 60°, sostenido 0.5 s.

### 4.6 Circuitos — test de integración (ya existen)

Mantener `basic` y `football` (+ opcionalmente 1 más de resistencia larga). **No**
crear 5: los circuitos miden comportamiento integrado, no métricas aisladas; cada
circuito extra es mantenimiento. Métricas agregadas por circuito:

| Métrica | Definición |
|---|---|
| `circuit.<name>.completed` | ¿terminó sin caerse? |
| `circuit.<name>.falls` | nº de caídas |
| `circuit.<name>.tracking_rmse` | error de tracking medio del circuito completo |
| `circuit.<name>.position_error` | desviación final vs trayectoria ideal (drift de yaw tipo exp_004 saldría aquí) |

---

## 5. Esquema del JSON de resultados

```json
{
  "checkpoint": "logs/hv-g1-manager/20260617_..._unified2/model_80896.pt",
  "checkpoint_id": "exp_008",
  "date": "2026-07-16",
  "benchmark_version": "1.0",
  "seeds": [42, 43, 44],
  "metrics": {
    "speed.forward":            {"mean": 1.73, "std": 0.05, "unit": "m/s"},
    "deadzone.forward":         {"mean": 0.15, "std": 0.00, "unit": "m/s"},
    "tracking.forward.rmse":    {"mean": 0.12, "std": 0.02, "unit": "m/s"},
    "gait.contact_ratio":       {"per_setpoint": {"1.0": 0.65, "2.0": 0.18}},
    "robustness.push.front":    {"mean": 45.0, "std": 5.0, "unit": "N·s"},
    "circuit.football.completed": true
  }
}
```

- `benchmark_version` para invalidar comparaciones si cambia la definición de una métrica.
- Métricas no evaluadas → ausentes (no `null`), así el informe distingue "no corrido" de "falló".

---

## 6. Informe comparativo (`report.py`)

Entrada: todos los JSON de `results/`. Salida: `results/REPORT.md`:

1. **Tabla principal** — filas = métricas, columnas = checkpoints, mejor valor en negrita.
2. **Radar chart** — 6 ejes agregados (velocidad, precisión, agilidad, marcha, robustez, terreno) normalizados 0-1 sobre el mejor valor observado; un polígono por checkpoint.
3. **Deltas vs baseline** — columna de % de cambio respecto a un checkpoint de referencia (p. ej. el .onnx upstream `fastsac_g1_29dof`).

---

## 7. Fases de implementación

| Fase | Contenido | Esfuerzo | Dependencias |
|---|---|---|---|
| **1** | `metrics.py` + ramp tests (vx/vy/vrz) + turn test + runner + JSON. Cubre `speed.*`, `deadzone.*`, `tracking.*`, `agility.*` | ~2-3 días | Ninguna — solo lee npz que ya generamos |
| **2** | Gait probe + detección de contacto. Cubre `gait.*`, `stability.feet` | ~2 días | Decidir contacto por altura vs ampliar recorder |
| **3** | Push recovery determinista sobre `EvalPushCallback`. Cubre `robustness.push.*` | ~1-2 días | Fase 1 (runner) |
| **4** | Terrain gauntlet. Cubre `stability.falls.*` | ~2-3 días | Reutilizar terrenos del training en eval |
| **5** | `report.py`: tabla + radar + deltas. Métricas de circuitos | ~1-2 días | Fases 1-2 mínimo |

**Fase 1 ya da valor**: podríamos comparar exp_007/exp_008/exp_009/upstream con números
esta misma semana, y responder cuantitativamente si exp_009 arregla el lean del sprint.

---

## 8. Decisiones abiertas (para discutir)

1. **Contacto de pies**: ¿estimar por altura/velocidad del pie desde `body_pos_w`
   (0 trabajo en el recorder, ~2 cm de error) o ampliar el recorder para guardar
   fuerzas de contacto del simulador (más preciso, toca `recording.py`)?
   *Propuesta: empezar por altura, migrar si el ruido molesta.*
2. **Repeticiones**: ¿N=3 semillas es suficiente? En sim con física determinista
   quizá baste N=1 + semillas distintas solo en push/terrain (que tienen aleatoriedad).
3. **Baseline de referencia**: ¿upstream `fastsac_g1_29dof.onnx` o exp_001?
4. **Dónde corren los benchmarks**: ¿siempre headless en el container (CI-able a futuro)?
   ¿Lo metemos en un workflow de GitHub Actions más adelante?
5. **Pelota física** (`robustness.ballhit.*` original): ¿la queremos como métrica o
   solo como demo? Propuesta: impulso de fuerza como métrica, pelota como demo futura.
6. **Umbral de caída** (0.4 m / 60°): ¿consenso con estos valores?

---

## 9. Fuera de alcance (por ahora)

- Evaluación en robot real (el benchmark es sim-only; correlación sim-real es otro proyecto).
- Métricas de eficiencia energética (cost of transport) — fácil de añadir después
  (torques ya se graban), pero no bloquea la v1.
- UI interactiva — el informe MD versionado en git cubre la necesidad de discusión.
