#!/bin/bash
# Evalúa un checkpoint con el eval_agent.py de holosoma.
# Ejecutar DENTRO del container con el entorno hsmujoco activado.
#
# Uso:
#   bash eval_checkpoint.sh <ruta_checkpoint.pt> [pasos_max]
#
# Ejemplo:
#   bash eval_checkpoint.sh logs/hv-g1-manager/<run>/model_24999.pt 2000
#
# Notas:
# - eval_agent.py carga la config guardada junto al checkpoint automáticamente
# - eval usa 1 env con visualización (eval_overrides del experimento)
# - para grabar trayectoria: añadir --recording.enabled --recording.output-path out.npz
# - para testear robustez con pushes: añadir --push.enabled

set -euo pipefail

CHECKPOINT="${1:?Uso: eval_checkpoint.sh <checkpoint.pt> [pasos_max]}"
MAX_STEPS="${2:-2000}"

if [ ! -f "$CHECKPOINT" ]; then
    echo "ERROR: checkpoint no encontrado: $CHECKPOINT" >&2
    exit 1
fi

echo "=== Evaluando: $CHECKPOINT (max $MAX_STEPS pasos) ==="

# Backend classic para eval: 1 env no necesita GPU y el rendering de Warp
# tiene un bug (shape mismatch en ten_J al extraer render data)
python src/holosoma/holosoma/eval_agent.py \
    --checkpoint "$CHECKPOINT" \
    --training.max-eval-steps "$MAX_STEPS" \
    --simulator.config.mujoco-backend CLASSIC \
    --randomization.ignore-unsupported True
