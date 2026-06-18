HOLOSOMA_DIR   := /home/maguelo/Workspace/holosoma
HUMANOIDS_DIR  := $(HOLOSOMA_DIR)
IMAGE          := holosoma-mujoco-lite:latest
CONTAINER      := holosoma-mujoco
LOGS_DIR       := $(HOLOSOMA_DIR)/logs

# Checkpoint y preset por defecto (sobreescribir desde CLI)
CHECKPOINT     ?=
PRESET         ?=
MAX_STEPS      ?= 500
NPZ            ?= /tmp/eval_out.npz

# ── Docker ─────────────────────────────────────────────────────────────────────

.PHONY: start
start:  ## Crear o arrancar el container del simulador
	xhost +local:docker 2>/dev/null || true
	@if docker ps -a --format '{{.Names}}' | grep -q '^$(CONTAINER)$$'; then \
	  echo "Arrancando container existente $(CONTAINER)..."; \
	  docker start $(CONTAINER); \
	else \
	  echo "Creando container $(CONTAINER)..."; \
	  docker run -d --name $(CONTAINER) \
	    --gpus all \
	    -v $(HOLOSOMA_DIR):/workspace \
	    -v /tmp/.X11-unix:/tmp/.X11-unix \
	    -e DISPLAY=$(DISPLAY) \
	    -w /workspace \
	    $(IMAGE) sleep infinity; \
	fi

.PHONY: stop
stop:  ## Parar el container (sin borrarlo)
	docker stop $(CONTAINER)

.PHONY: restart
restart: stop start  ## Reiniciar el container

.PHONY: destroy
destroy:  ## Borrar el container completamente (los logs y checkpoints están en el host, no se pierden)
	docker rm -f $(CONTAINER) 2>/dev/null || true

.PHONY: shell
shell: start  ## Abrir bash interactivo en el container con el entorno activado
	docker exec -it -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && bash"

.PHONY: setup
setup: start  ## Instalar entorno conda dentro del container (solo la primera vez, ~5-10 min)
	docker exec -it -w /workspace $(CONTAINER) bash -c \
	  "bash scripts/setup_mujoco.sh"

# ── Training ───────────────────────────────────────────────────────────────────

.PHONY: train-walking
train-walking: start  ## exp_001: walking desde cero
	docker exec -d -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/train_agent.py exp:g1-29dof simulator:mjwarp \
	   > /workspace/logs/train_walking.log 2>&1"
	@echo "Training walking lanzado en background — logs: $(LOGS_DIR)/train_walking.log"

.PHONY: train-jog
train-jog: start  ## exp_002: jog/trote con warm-start desde walking
	docker exec -d -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/train_agent.py exp:g1-29dof-running simulator:mjwarp \
	     --training.checkpoint logs/hv-g1-manager/20260605_141231-g1_29dof_manager-locomotion/model_24999.pt \
	   > /workspace/logs/train_jog.log 2>&1"
	@echo "Training jog lanzado en background — logs: $(LOGS_DIR)/train_jog.log"

.PHONY: train-strafe
train-strafe: start  ## exp_003: strafe/portero con warm-start desde walking
	docker exec -d -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/train_agent.py exp:g1-29dof-strafe simulator:mjwarp \
	     --training.checkpoint logs/hv-g1-manager/20260605_141231-g1_29dof_manager-locomotion/model_24999.pt \
	   > /workspace/logs/train_strafe.log 2>&1"
	@echo "Training strafe lanzado en background — logs: $(LOGS_DIR)/train_strafe.log"

.PHONY: train-sprint
train-sprint: start  ## exp_006: sprint con warm-start desde jog (exp_004 checkpoint)
	docker exec -d -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/train_agent.py exp:g1-29dof-sprint3 simulator:mjwarp \
	     --training.checkpoint logs/hv-g1-manager/20260612_090005-g1_29dof_sprint_manager-locomotion/model_45899.pt \
	   > /workspace/logs/train_sprint.log 2>&1"
	@echo "Training sprint lanzado en background — logs: $(LOGS_DIR)/train_sprint.log"

.PHONY: train-unified
train-unified: start  ## exp_007: unified locomotion (parado→sprint + backwards + giros) warm-start desde sprint3
	docker exec -d -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/train_agent.py exp:g1-29dof-unified simulator:mjwarp \
	     --training.checkpoint logs/hv-g1-manager/20260615_071843-g1_29dof_sprint3_manager-locomotion/model_55898.pt \
	   > /workspace/logs/train_unified.log 2>&1"
	@echo "Training unified lanzado en background — logs: $(LOGS_DIR)/train_unified.log"

.PHONY: train-unified2
train-unified2: start  ## exp_008: unified etapa 2 — gait fijo 0.5±0.1s para estabilizar sprint, warm-start desde unified
	docker exec -d -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/train_agent.py exp:g1-29dof-unified2 simulator:mjwarp \
	     --training.checkpoint logs/hv-g1-manager/20260616_202634-g1_29dof_unified_manager-locomotion/model_70897.pt \
	   > /workspace/logs/train_unified2.log 2>&1"
	@echo "Training unified2 lanzado en background — logs: $(LOGS_DIR)/train_unified2.log"

.PHONY: train-unified3
train-unified3: start  ## exp_009: unified stage 3 — base_height penalty + stronger orientation to fix forward lean
	docker exec -d -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/train_agent.py exp:g1-29dof-unified3 simulator:mjwarp \
	     --training.checkpoint logs/hv-g1-manager/20260617_214143-g1_29dof_unified2_manager-locomotion/model_80896.pt \
	   > /workspace/logs/train_unified3.log 2>&1"
	@echo "Training unified3 launched in background — logs: $(LOGS_DIR)/train_unified3.log"

.PHONY: train-custom
train-custom: start  ## Entrenamiento custom: make train-custom EXP=exp:g1-29dof-sprint3 CHECKPOINT=logs/.../model.pt
	@[ -n "$(EXP)" ] || (echo "Uso: make train-custom EXP=exp:<nombre> [CHECKPOINT=<ruta>]" && exit 1)
	docker exec -d -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/train_agent.py $(EXP) simulator:mjwarp \
	     $$([ -n '$(CHECKPOINT)' ] && echo '--training.checkpoint $(CHECKPOINT)') \
	   > /workspace/logs/train_custom.log 2>&1"
	@echo "Training $(EXP) lanzado — logs: $(LOGS_DIR)/train_custom.log"

# ── Eval ───────────────────────────────────────────────────────────────────────

.PHONY: eval-walking
eval-walking: start  ## Eval walking forward 1.0 m/s (exp_001)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260605_141231-g1_29dof_manager-locomotion/model_24999.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_walking.npz \
	     command:g1-29dof-walk-forward"

.PHONY: eval-turn
eval-turn: start  ## Eval walking with random commands (turns, lateral, etc.) (exp_001)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260605_141231-g1_29dof_manager-locomotion/model_24999.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_turn.npz"

.PHONY: eval-jog
eval-jog: start  ## Eval jog/trote a 1.0 m/s (exp_002)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260610_070927-g1_29dof_running_manager-locomotion/model_35900.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_jog.npz \
	     command:g1-29dof-run-forward"

.PHONY: eval-strafe-left
eval-strafe-left: start  ## Eval strafe izquierda 1.5 m/s (exp_003)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260611_230114-g1_29dof_strafe_manager-locomotion/model_34998.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_strafe_left.npz \
	     command:g1-29dof-strafe-left"

.PHONY: eval-strafe-right
eval-strafe-right: start  ## Eval strafe derecha 1.5 m/s (exp_003)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260611_230114-g1_29dof_strafe_manager-locomotion/model_34998.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_strafe_right.npz \
	     command:g1-29dof-strafe-right"

.PHONY: eval-sprint
eval-sprint: start  ## Eval sprint a 2.0 m/s (exp_006)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260615_071843-g1_29dof_sprint3_manager-locomotion/model_55898.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_sprint.npz \
	     command:g1-29dof-sprint-forward"

.PHONY: eval-unified-sprint
eval-unified-sprint: start  ## Eval unified: sprint 2.0 m/s hacia delante (exp_007)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260616_202634-g1_29dof_unified_manager-locomotion/model_70897.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_unified_sprint.npz \
	     command:g1-29dof-sprint-forward"

.PHONY: eval-unified-backward
eval-unified-backward: start  ## Eval unified: marcha atrás 1.0 m/s (exp_007)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260616_202634-g1_29dof_unified_manager-locomotion/model_70897.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_unified_backward.npz \
	     command:g1-29dof-unified-backward"

.PHONY: eval-unified-turn
eval-unified-turn: start  ## Eval unified: giro en el sitio 1.0 rad/s (exp_007)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint logs/hv-g1-manager/20260616_202634-g1_29dof_unified_manager-locomotion/model_70897.pt \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path /tmp/eval_unified_turn.npz \
	     command:g1-29dof-unified-turn"

.PHONY: eval-custom
eval-custom: start  ## Eval custom: make eval-custom CHECKPOINT=logs/.../model.pt PRESET=command:g1-29dof-run-forward
	@[ -n "$(CHECKPOINT)" ] || (echo "Uso: make eval-custom CHECKPOINT=<ruta> [PRESET=command:...] [MAX_STEPS=500] [NPZ=/tmp/out.npz]" && exit 1)
	xhost +local:docker 2>/dev/null || true
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python src/holosoma/holosoma/eval_agent.py \
	     --checkpoint $(CHECKPOINT) \
	     --training.max-eval-steps $(MAX_STEPS) \
	     --simulator.config.mujoco-backend CLASSIC \
	     --randomization.ignore-unsupported True \
	     --recording.config.enabled \
	     --recording.config.output-path $(NPZ) \
	     $(PRESET)"

# ── Logs ───────────────────────────────────────────────────────────────────────

.PHONY: logs-training
logs-training:  ## Seguir el log del último training lanzado (LOGFILE=train_sprint.log)
	tail -f $(LOGS_DIR)/$(or $(LOGFILE),train_sprint.log) | grep --line-buffered -E "Learning iteration|mean reward|rew_tracking_lin_vel|Error|Traceback"

.PHONY: metrics
metrics:  ## Extraer métricas de un run: make metrics RUN=logs/hv-g1-manager/<run>
	@[ -n "$(RUN)" ] || (echo "Uso: make metrics RUN=logs/hv-g1-manager/<run-dir>" && exit 1)
	docker exec -w /workspace $(CONTAINER) bash -c \
	  "source scripts/source_mujoco_setup.sh && \
	   python3 /workspace/loop/extract_metrics.py /workspace/$(RUN)"

.PHONY: help
help:  ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
