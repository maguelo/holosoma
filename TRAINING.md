# Training a Humanoid Robot — Tutorial

Goal: train a new locomotion policy for the G1-29DOF using the holosoma pipeline.

---

## Objective: is running possible?

Yes, it is technically possible. But there are important nuances:

**Running** implies an aerial phase (both feet off the ground simultaneously), which requires:
- A reward function that incentivises high speeds and the correct stride pattern
- Much more training compute than walking
- The Quadro T1000 (4GB) laptop GPU is limited for parallel training — IsaacSim needs ≥8GB to run parallel environments efficiently

**Suggested more realistic progression:**
1. ✅ **Understand the pipeline** — reproduce the training of the current model
2. 🎯 **Walk faster** — increase the maximum velocity in the curriculum (from ~0.5 m/s to ~1.5 m/s)
3. 🏃 **Jog/run** — modify the reward to incentivise speeds >2 m/s and the running stride pattern

---

## How training works in holosoma

### Supported simulators

Training is **simulator-agnostic** — all three backends are integrated and interchangeable:

| Simulator | GPU | Parallel envs | Setup | Recommended for |
|---|---|---|---|---|
| **IsaacSim** | ✅ | Thousands | ~30GB, NGC account | Production, maximum throughput |
| **IsaacGym** | ✅ | Hundreds | Lighter than IsaacSim | Alternative to IsaacSim |
| **MuJoCo Classic** | ❌ CPU | 1 | Already installed | Debug, development |
| **MuJoCo Warp** | ✅ | Hundreds | setup_mujoco.sh | **Our case** (RTX 4070) |

**For us → MuJoCo Warp** is the right choice: MuJoCo is already installed, we don't need IsaacSim, and the RTX 4070 (12GB) can run hundreds of parallel environments.

```
MuJoCo Warp (training, parallel GPU)
    → generates .onnx checkpoint
        → MuJoCo Classic (sim-to-sim evaluation)
            → Real robot
```

### RL algorithm

The current model uses **FastSAC** (a variant of Soft Actor-Critic). The pipeline also supports PPO.

### Current reward function (G1-29DOF)

Defined in `src/holosoma/holosoma/config_values/loco/g1/reward.py`:

| Term | Weight | Description |
|---|---|---|
| `tracking_lin_vel` | +2.0 | Track commanded linear velocity |
| `tracking_ang_vel` | +1.5 | Track commanded angular velocity |
| `feet_phase` | +5.0 | Periodic step pattern (swing height: 9cm) |
| `alive` | +10.0 | Stay upright |
| `penalty_orientation` | -10.0 | Penalise torso tilt |
| `penalty_close_feet_xy` | -10.0 | Penalise feet too close together |
| `penalty_feet_ori` | -5.0 | Penalise incorrect foot orientation |
| `penalty_action_rate` | -2.0 | Penalise abrupt action changes |
| `penalty_ang_vel_xy` | -1.0 | Penalise unwanted torso rotation |

---

## Option A — Train with MuJoCo Warp (recommended)

**Requirements:** RTX 4070 (12GB) + NVIDIA driver ≥555 + CUDA 12.4

### Step 1 — Enable GPU in Docker (once on the host)

The container needs to see the GPU. Without this, `setup_mujoco.sh` fails with `No NVIDIA driver detected`.

```bash
# On the HOST (outside any container)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Recreate the inference container with GPU access
docker rm -f holosoma-inference-container
bash src/holosoma_inference/docker/run.sh
```

> **Ignorable warning:** `groups: cannot find name for group ID 992` — the host `docker` group
> has no name inside the container. Does not affect functionality.
>
> **Typical error:** `❌ ERROR: NVIDIA driver not found or too old` inside the container →
> the container was created without `--gpus all`. Fix: install NVIDIA Container Toolkit on the
> host and recreate the container.

### Step 2 — Enter the container and set up the environment

```bash
docker run -it --gpus all \
  -v /home/maguelo/Workspace/holosoma:/workspace \
  -w /workspace \
  holosoma-mujoco-lite:latest bash
```

Inside the container, the first time you need to install the environment (~5-10 min):

```bash
bash scripts/setup_mujoco.sh   # without --no-warp installs Warp automatically
source scripts/source_mujoco_setup.sh
```

On subsequent runs (if the container already has the environment):

```bash
source scripts/source_mujoco_setup.sh
```

### Step 3 — Launch training

```bash
# CPU — one environment (slow, only to verify the pipeline works)
python src/holosoma/holosoma/train_agent.py exp:g1-29dof simulator:mujoco

# GPU — MuJoCo Warp (what we use)
# Default is 4096 environments — too many for GPUs with limited VRAM
# Adjust --training.num-envs based on the GPU:
#   Quadro T1000 (4GB):  64-256 environments
#   RTX 4070 (12GB):     1024-2048 environments
python src/holosoma/holosoma/train_agent.py exp:g1-29dof simulator:mjwarp \
  --training.num-envs=256

# FastSAC (the pre-trained model's algorithm) with Warp
python src/holosoma/holosoma/train_agent.py exp:g1-29dof-fast-sac simulator:mjwarp \
  --training.num-envs=256
```

> **OOM error:** `Failed to allocate X bytes on device 'cuda:0'` → reduce `--training.num-envs`

Available experiments: `exp:g1-29dof`, `exp:g1-29dof-fast-sac`, `exp:g1-29dof-running`,
`exp:g1-29dof-strafe`, `exp:g1-29dof-unified`, `exp:g1-29dof-unified2`, `exp:t1-29dof`,
`exp:t1-29dof-fast-sac`, `exp:g1-29dof-wbt`, `exp:g1-29dof-wbt-fast-sac`

### Step 4 — Evaluate the generated checkpoint

#### Quick option: `eval_agent.py` (visualisation + trajectory recording)

Automatically loads the config saved with the checkpoint and accepts CLI overrides.

```bash
# On the HOST, once: allow X11 to the container
xhost +local:docker

# Container with GPU + display
docker run -it --gpus all \
  -v /home/maguelo/Workspace/holosoma:/workspace \
  -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY \
  -w /workspace holosoma-mujoco-lite:latest bash

# Inside the container
source scripts/source_mujoco_setup.sh
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/<run>/model_XXXX.pt \
  --training.max-eval-steps 2000 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True
```

Flags learned the hard way:

| Flag | Why |
|---|---|
| `--simulator.config.mujoco-backend CLASSIC` | Warp rendering has a bug (shape mismatch in `ten_J`). UPPERCASE — it's an enum |
| `--randomization.ignore-unsupported True` | MuJoCo Classic doesn't support mass randomization → without this, `RandomizerNotSupportedError` |
| `command:g1-29dof-run-forward` | Fixed command preset for controlled eval (see below) |
| `--recording.config.enabled --recording.config.output-path /tmp/rec.npz` | Records trajectory to NPZ. Flags go under `.config.`, not `--recording.enabled` |

**Fixed command in eval.** By default eval samples ONE random command at reset from the
training ranges (which is why the robot can "run sideways"). For controlled evaluation we
created fixed-range presets in `config_values/loco/g1/command.py`.

**Analysing the NPZ recording.** Useful channels: `commanded_velocity` (what the policy
receives), `root_lin_vel` and `root_pos` (what the robot does). If the NPZ is in `/tmp`
of the container: `docker cp <container>:/tmp/rec.npz /tmp/`. Comparing commanded vs actual
velocity distinguishes "the command doesn't arrive" from "the policy doesn't track it".

#### Movement catalogue

Each movement = a checkpoint + a command preset (`command:...`). All are launched with
the same template (inside the container, after `source scripts/source_mujoco_setup.sh`):

```bash
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint <CHECKPOINT> \
  --training.max-eval-steps 2000 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  <COMMAND_PRESET>
```

| Movement | Checkpoint | Preset | Command sent |
|---|---|---|---|
| **Walking** (random) | `model_24999.pt` (exp_001) | *(none)* | random: x,y ∈ ±1.0, yaw ±1.0 |
| **Jog** (≤1.0 m/s) | `model_35900.pt` (exp_002) | `command:g1-29dof-run-forward` | `[1.0, 0, 0]` fixed |
| **Sprint** (1.73 m/s) | `model_55898.pt` (exp_006) | `command:g1-29dof-sprint-forward` | `[2.0, 0, 0]` fixed |
| **Strafe left** (1.5 m/s) | `model_34998.pt` (exp_003) | `command:g1-29dof-strafe-left` | `[0, 1.5, 0]` fixed |
| **Strafe right** (1.5 m/s) | `model_34998.pt` (exp_003) | `command:g1-29dof-strafe-right` | `[0, -1.5, 0]` fixed |
| **Unified forward** | `model_70897.pt` (exp_007) | `command:g1-29dof-sprint-forward` | `[2.0, 0, 0]` fixed |
| **Unified backward** | `model_70897.pt` (exp_007) | `command:g1-29dof-unified-backward` | `[-1.0, 0, 0]` fixed |
| **Unified turn** | `model_70897.pt` (exp_007) | `command:g1-29dof-unified-turn` | `[0, 0, 1.0]` fixed |

⚠️ **The `gait_period` in the eval preset must match the training checkpoint's gait_period**
(walking 1.0s · jog 0.5s · strafe 0.8s · sprint 0.5s · unified 0.5-0.7s). The eval preset
replaces the ENTIRE command manager, including the gait. A mismatched gait degrades locomotion.

The registered names are in `config_values/command.py` (`DEFAULTS`): Python underscores
become hyphens in the CLI (`g1_29dof_strafe_left` → `command:g1-29dof-strafe-left`).

#### Full option: simulator + inference (sim-to-real flow)

```bash
# Terminal 1 — simulator
python3 src/holosoma/holosoma/run_sim.py robot:g1-29dof

# Terminal 2 — policy (single model)
python3 src/holosoma_inference/holosoma_inference/run_policy.py inference:g1-29dof-loco \
  --task.model-path <path-to-checkpoint.onnx> \
  --task.no-use-joystick \
  --task.interface lo

# Terminal 2 — dual-mode policy (two models, switch with X / x key)
python3 src/holosoma_inference/holosoma_inference/run_policy.py inference:g1-29dof-loco \
  --task.model-path <primary.onnx> \
  --task.no-use-joystick \
  --task.interface lo \
  --secondary.task.model-path <secondary.onnx>
```

> **Note:** `holosoma_inference` must be installed in the conda environment:
> `pip install -e src/holosoma_inference`

---

## Option B — Train with IsaacSim

**Requirements:** GPU ≥8GB + NVIDIA NGC account + ~30GB disk

### Step 1 — Build the image

```bash
docker login nvcr.io
docker build -f docker/isaacsim.Dockerfile -t holosoma-isaacsim \
  /home/miguel/Workspace/holosoma
```

### Step 2 — Launch training

```bash
docker run -it --gpus all --name holosoma-isaacsim-container \
  -v /home/miguel/Workspace/holosoma:/workspace/holosoma \
  -w /workspace/holosoma \
  holosoma-isaacsim

python src/holosoma/holosoma/train_agent.py exp:g1-29dof simulator:isaacsim
```

---

## Modifying behaviour: from walking to running

### Step 1 — Walk faster

Edit `src/holosoma/holosoma/config_values/loco/g1/reward.py`:
- Increase weight of `tracking_lin_vel` (from 2.0 to ~3.0)
- Adjust the velocity curriculum to reach 1.5 m/s

### Step 2 — Jog / run

Additional reward changes:
- Expand target velocity range (>2 m/s)
- Increase `swing_height` in `feet_phase` (from 9cm to ~15cm)
- Reduce `gait_period` for faster strides
- Ensure `tracking_lin_vel` weight > `feet_phase` weight (critical — see lessons learned)

---

## Experiment history: what changed in each one

Full record in `experiments/EXPERIMENTS.md`. Configs live in
`src/holosoma/holosoma/config_values/loco/g1/{command,reward,experiment}.py`.

### exp_001 — walking (`exp:g1-29dof`) ✅ promoted

Default repo config, no changes. From scratch, 25k iters, mjwarp 4096 envs (~15h).
- Command: x,y ∈ ±1.0 m/s, yaw ±1.0, gait 1.0s, resampling 10s, stand_prob 0.2
- Result: tracking_lin 0.91, no falls → checkpoint `model_24999.pt`

### exp_002 — running (`exp:g1-29dof-running`) ⚠️ promoted as "jog"

Warm-start from walking. Key changes: lin_vel_x [-0.5, 3.5], gait 0.5s, swing_height 0.15.
- Result: learned to jog (64% aerial phase) but ceiling ~0.9 m/s due to local optimum
- Checkpoint `model_35900.pt`: usable as jog/trot skill with commands ≤1.0 m/s

### exp_003 — strafe / goalkeeper (`exp:g1-29dof-strafe`) ✅ promoted

Warm-start from walking. Key changes: lin_vel_y ±1.5, gait 0.8s, resampling 5s.
- Validated in visualiser: lateral movement at 1.5 m/s works correctly

### exp_004–006 — sprint (`sprint` → `sprint2` → `sprint3`) ✅ promoted

Three iterations to achieve real sprint. Critical lesson: **`feet_phase` weight must not
exceed `tracking_lin_vel` weight** or the policy learns to jog in place.

| Exp | Problem | Fix |
|---|---|---|
| exp_004 | Runs but drifts 52° yaw | yaw ±0.1, tracking_ang 2.0 |
| exp_005 | Yaw fixed but jogs in place (feet_phase 5.0 > tracking_lin 3.0) | Swap weights |
| **exp_006** | ✅ **Real sprint**: 1.73 m/s, 82% aerial phase, 26° yaw drift | tracking_lin **5.0**, feet_phase **2.0** |

### exp_007 — unified locomotion ⚠️ partial

Full range [-1.5, 3.0] m/s + backwards + turns + variable gait [0.4, 1.0]s.
Backwards ✅, turns ✅, sprint unstable ❌ (variable gait causes instability at high speed).

### exp_008 — unified stage 2 🔄 in progress

Narrow gait to [0.4, 0.6]s to fix sprint instability while keeping backwards and turns.

---

## Lessons learned

### What worked

- **RTX 4070 (12GB) runs 4096 envs** with MuJoCo Warp without OOM (~15h per 25k iters)
- **Warm-start from a checkpoint** works well: running started from walking's `model_24999.pt`
  and recovered episode_length from 13.7 → 1001 in ~3k iterations
- **The plateau is visible**: reward and tracking stop improving around ~28k iters. Training
  beyond that adds nothing

### How to interpret metrics (normalise by weight!)

`Episode/rew_tracking_lin_vel` is reward, not tracking. Divide by the term's weight to compare:

| Run | rew_tracking_lin_vel | Weight | Real tracking |
|---|---|---|---|
| exp_001 walking | 0.91 | 1.0 | ~0.91 ✅ |
| exp_002 running | 1.63 | 3.0 | ~0.54 ⚠️ |

### The jog-in-place local optimum

With a wide command range without curriculum, the policy finds a local optimum: **at high
commands it jogs in place** (earns `alive` + `feet_phase`, avoids penalties, and failed
tracking is diluted in the mean by low commands it does track).

**Fix**: `tracking_lin_vel` weight must be higher than `feet_phase` weight (lesson from
exp_005/006: tracking_lin 5.0, feet_phase 2.0).

### Known crashes

- **`RuntimeError: normal expects all elements of std >= 0.0`** at the end of a long Warp
  run: sudden NaN from physics explosion. The last checkpoint before the crash is usable.
- In eval: `set_is_evaluating()` zeroes commands, but `reset_all()` resamples them from
  preset ranges — the command DOES reach the policy (verified with `commanded_velocity` NPZ channel).

---

## References

- Reward terms: `src/holosoma/holosoma/managers/reward/terms/locomotion.py`
- G1 reward config: `src/holosoma/holosoma/config_values/loco/g1/reward.py`
- Training entry point: `src/holosoma/holosoma/train_agent.py`
- Experiment configs: `src/holosoma/holosoma/config_values/loco/g1/experiment.py`
