# Experiment Registry

One experiment = one row. Details and metrics in `experiments/<id>/`.

| ID | Date | Skill | Base | Key changes | Iters | Result | Decision |
|----|------|-------|------|-------------|-------|--------|----------|
| exp_001 | 2026-06-05 | walking | scratch | default config `exp:g1-29dof`, mjwarp 4096 envs | 25k | reward 35.2, tracking_lin 0.91, ep_len 1001/1001, 0 falls at end | ✅ PROMOTED — locomotion baseline |
| exp_002 | 2026-06-10 | running | exp_001 (model_24999.pt) | lin_vel_x [-0.5,3.5], gait 0.5s, swing 0.15m, sigma 0.5, adjusted weights | 11k (24999→35995, NaN crash) | learned to JOG for real (64% aerial phase, verified in NPZ) but ceiling ~0.9 m/s; at 2 m/s jogs in place (local optimum) | ⚠️ PROMOTED AS "jog/trot" (model_35900.pt, use with commands ≤1.0 m/s) — sprint at 2-3.5 m/s pending (needs curriculum) |
| exp_003 | 2026-06-12 | strafe (goalkeeper) | exp_001 (model_24999.pt) | lin_vel_y ±1.5, x/yaw ±0.5, gait 0.8s, resampling 5s, tracking 3.0/σ0.25, close_feet -5/0.10 | 10k (24999→34998, no crash) | ep_len 1001/1001, mean tracking_lin ~0.50 (penalised by 5s resampling); eval visual ✅ | ✅ PROMOTED — lateral strafe 1.5 m/s works well in visualiser (eval_agent.py) |
| exp_004 | 2026-06-12 | sprint stage 1 | exp_002 (model_35900.pt, jog) | lin_vel_x [0.5, 2.0] (no hiding place), stand_prob 0, y/yaw ±0.3, gait 0.5±0.05, running reward | 10k (35900→45899, no crash) | tracking_lin 2.51/3.0 = **~0.84** (vs 0.54 in exp_002), ep_len 996/1001 | ⚠️ PROMOTED AS "sprint stage 1" — runs fast but drifts 52° in 10s (yaw drift); fixed in exp_005 |
| exp_005 | 2026-06-15 | sprint stage 2 (yaw fix) | exp_004 (model_45899.pt) | lin_vel_x [1.0, 3.0], yaw ±0.1, tracking_ang 2.0/σ0.15, penalty_ang_vel_xy -2.0, swing 0.15m | 10k (45899→55898, no crash) | tracking_lin 1.56/3.0 = ~0.52, tracking_ang 1.23/2.0 ✅; but **jogs in place** in eval (vx=0.07 with cmd 2.47) | ❌ DISCARDED — feet_phase (5.0) > tracking_lin (3.0): jog-in-place local optimum. Fix in exp_006: lower feet_phase, raise tracking_lin |
| exp_006 | 2026-06-15 | sprint stage 3 (reward fix) | exp_004 (model_45899.pt) | tracking_lin **5.0**/σ0.5, feet_phase **2.0**, lin_vel_x [1.0, 2.5], yaw ±0.2, tracking_ang 2.0/σ0.2 | 10k (45899→55898, no crash) | tracking_lin 4.05/5.0=0.81 ✅, ep_len 1001; eval: vx=1.73 m/s (cmd 2.1), 82% aerial phase, yaw drift -26° | ✅ PROMOTED — real sprint with aerial phase; yaw drift improved vs exp_004 (52°→26°) but could be reduced further |
| exp_007 | 2026-06-16 | unified locomotion | exp_006 (model_55898.pt) | lin_vel_x [-1.5, 3.0] (backwards+sprint), yaw ±1.0, gait [0.4,1.0]s variable, tracking_lin 5.0/feet_phase 2.0, 15k iters | 15k (55898→70897, no crash) | tracking_lin 3.51/5.0=0.70 ⚠️, tracking_ang 1.06/2.0=0.53, ep_len 1001/1001 ✅, no falls; eval: backwards ✅, turn ✅, sprint very unstable ❌ | ⚠️ PARTIAL PROMOTION — backwards+turns ok, sprint degraded by variable gait. Fixed in exp_008: narrow gait |
| exp_008 | 2026-06-17 | unified stage 2 (sprint fix) | exp_007 (model_70897.pt) | gait 0.5±0.1→[0.4,0.6]s (removes slow cadences at high speed), rest unchanged | 10k (70897→80896, no crash) | tracking_lin 3.60/5.0=0.72 ✅ (+2% vs exp_007), tracking_ang 1.08/2.0=0.54, ep_len 1001/1001 ✅; eval: sprint still very unstable, robot about to fall, COM too far forward | ⚠️ PARTIAL — gait fixed but torso leans forward during sprint. Fix in exp_009: base_height penalty + stronger orientation |
| exp_009 | 2026-06-18 | unified stage 3 (forward lean fix) | exp_008 (model_80896.pt) | penalty_orientation -10→**-20**, add **base_height -3.0** (desired 0.89m), rest unchanged | — | ⏸ READY TO LAUNCH |

## Conventions

- **Base**: checkpoint to warm-start from, or `scratch`
- **Decision**: ✅ PROMOTED / ❌ DISCARDED / 🔄 IN PROGRESS — with reason
- When closing an experiment: run `loop/extract_metrics.py` on the run and save the JSON in `experiments/<id>/metrics.json`
- Promoted checkpoints: record exact `.pt`/`.onnx` path here

## Promoted checkpoints

| Skill | Checkpoint | Run |
|-------|-----------|-----|
| walking | `logs/hv-g1-manager/20260605_141231-g1_29dof_manager-locomotion/model_24999.{pt,onnx}` | exp_001 |
| jog/trot (≤1.0 m/s, with aerial phase) | `logs/hv-g1-manager/20260610_070927-g1_29dof_running_manager-locomotion/model_35900.{pt,onnx}` | exp_002 |
| sprint (1.73 m/s real, 82% aerial phase) | `logs/hv-g1-manager/20260615_071843-g1_29dof_sprint3_manager-locomotion/model_55898.{pt,onnx}` | exp_006 |
| unified (standing→sprint + backwards + turns) | `logs/hv-g1-manager/20260616_202634-g1_29dof_unified_manager-locomotion/model_70897.{pt,onnx}` | exp_007 🔄 eval pending |

---

## Eval commands per experiment

All run **inside the container** after `source scripts/source_mujoco_setup.sh`.
The NPZ is recorded to `/tmp/` in the container — to copy to host: `docker cp <container>:/tmp/eval_xxx.npz /tmp/`.

### exp_001 — walking

```bash
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/20260605_141231-g1_29dof_manager-locomotion/model_24999.pt \
  --training.max-eval-steps 500 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  --recording.config.enabled \
  --recording.config.output-path /tmp/eval_walking.npz
```

*(No command preset — randomly samples x,y ∈ ±1.0 m/s, yaw ±1.0)*

### exp_002 — jog / trot (≤1.0 m/s)

```bash
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/20260610_070927-g1_29dof_running_manager-locomotion/model_35900.pt \
  --training.max-eval-steps 500 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  --recording.config.enabled \
  --recording.config.output-path /tmp/eval_jog.npz \
  command:g1-29dof-run-forward
```

*(Preset `run-forward`: lin_vel_x [1.0, 1.0], gait 0.5s — real ceiling of this policy ~0.85 m/s)*

### exp_003 — strafe / lateral goalkeeper (1.5 m/s)

```bash
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/20260611_230114-g1_29dof_strafe_manager-locomotion/model_34998.pt \
  --training.max-eval-steps 500 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  --recording.config.enabled \
  --recording.config.output-path /tmp/eval_strafe_left.npz \
  command:g1-29dof-strafe-left
```

```bash
# Strafe right
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/20260611_230114-g1_29dof_strafe_manager-locomotion/model_34998.pt \
  --training.max-eval-steps 500 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  --recording.config.enabled \
  --recording.config.output-path /tmp/eval_strafe_right.npz \
  command:g1-29dof-strafe-right
```

### exp_006 — sprint (1.73 m/s real, 82% aerial phase)

```bash
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/20260615_071843-g1_29dof_sprint3_manager-locomotion/model_55898.pt \
  --training.max-eval-steps 500 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  --recording.config.enabled \
  --recording.config.output-path /tmp/eval_sprint.npz \
  command:g1-29dof-sprint-forward
```

*(Preset `sprint-forward`: lin_vel_x [2.0, 2.0], gait 0.5s)*

### exp_007 — unified locomotion (standing → sprint + backwards + turns)

Update `<run_unified>` and `model_XXXX` once training finishes.

```bash
# Sprint 2.0 m/s forward
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/20260616_202634-g1_29dof_unified_manager-locomotion/model_70897.pt \
  --training.max-eval-steps 500 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  --recording.config.enabled \
  --recording.config.output-path /tmp/eval_unified_sprint.npz \
  command:g1-29dof-sprint-forward

# Backwards 1.0 m/s
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/20260616_202634-g1_29dof_unified_manager-locomotion/model_70897.pt \
  --training.max-eval-steps 500 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  --recording.config.enabled \
  --recording.config.output-path /tmp/eval_unified_backward.npz \
  command:g1-29dof-unified-backward

# Turn in place 1.0 rad/s
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint logs/hv-g1-manager/20260616_202634-g1_29dof_unified_manager-locomotion/model_70897.pt \
  --training.max-eval-steps 500 \
  --simulator.config.mujoco-backend CLASSIC \
  --randomization.ignore-unsupported True \
  --recording.config.enabled \
  --recording.config.output-path /tmp/eval_unified_turn.npz \
  command:g1-29dof-unified-turn
```
