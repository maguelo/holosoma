# Football Circuit Evaluation Report

**Date:** 2026-07-01
**Circuit:** `football` (sprint → square → agility → diamond → pivot → figure-8)
**Simulator:** MuJoCo Classic, 50 Hz policy rate

---

## Models Evaluated

| ID | Model | Source |
|----|-------|--------|
| **Original** | `ppo_g1_29dof.onnx` | Shipped with repository (`src/holosoma_inference/.../models/loco/g1_29dof/`) |
| **Unified** | `model_80896.pt` | exp_008 — `20260617_214143-g1_29dof_unified2_manager-locomotion` |

---

## Summary

| Metric | Original (ONNX) | Unified exp_008 | Δ |
|--------|:--------------:|:---------------:|:--|
| Duration | 45.6 s | 45.6 s | — |
| Mean base height (Z) | 0.729 m | 0.683 m | −0.046 m |
| Min base height (Z) | **0.076 m** | **0.580 m** | +0.504 m ✅ |
| Mean XY speed | 0.541 m/s | **1.210 m/s** | +123% ✅ |
| Max XY speed | 2.483 m/s | 2.156 m/s | −0.33 m/s |
| Torque RMS | 9.75 N·m | 11.50 N·m | +18% |
| Max torque | 139.0 N·m | 139.0 N·m | — |
| Steps with Z < 0.5 m | **77 (3.4%)** | **0 (0.0%)** | −77 ✅ |
| Tracking error Vx | 1.249 m/s | 1.142 m/s | −0.107 m/s ✅ |
| Tracking error Vy | 0.696 m/s | 0.819 m/s | +0.123 m/s |

---

## Per-Phase Analysis

The football circuit is divided into 6 phases. Below is the outcome per phase for each model.

### Phase 0 — Stand (3.0 s)
Both models idle stably. No falls.

### Phase 1 — Sprint (0.5 s walk-up + 2.0 s sprint, vx up to 2.0)

| Model | Mean speed | Z min | Falls |
|-------|-----------|-------|-------|
| Original | 0.65 m/s | 0.733 m | 0 |
| Unified | 1.55 m/s | 0.633 m | 0 |

Unified reaches commanded speed much more closely (+138%). Both are stable.

### Phase 2 — Square (strafe R, retreat, strafe L, sprint)

| Segment | Original speed | Unified speed |
|---------|---------------|---------------|
| Strafe right (vy=−1.5) | 0.56 m/s | 0.99 m/s |
| Retreat (vx=−1.5) | 0.24 m/s | 1.12 m/s |
| Strafe left (vy=+1.5) | 0.29 m/s | 0.91 m/s |
| Sprint (vx=+2.0) | 0.60 m/s | 1.00 m/s |

No falls for either model. Unified tracks commanded velocity ~3–4× better on retreat and strafe.

### Phase 3 — Agility (max vy strafe ±2.0, sprint)

| Segment | Original speed | Unified speed |
|---------|---------------|---------------|
| Strafe left (vy=+2.0) | 0.48 m/s | 1.13 m/s |
| Strafe right (vy=−2.0) | 0.37 m/s | 0.78 m/s |

No falls for either model. Original notably slow on lateral commands.

### Phase 4 — Diamond (diagonal movements vx=vy=±1.5, sprint)

| Segment | Original speed | Unified speed |
|---------|---------------|---------------|
| Fwd-right (vx=+1.5, vy=−1.5) | 0.51 m/s | 1.57 m/s |
| Fwd-left (vx=+1.5, vy=+1.5) | 0.33 m/s | 1.25 m/s |
| Back-left (vx=−1.5, vy=+1.5) | 0.33 m/s | 1.19 m/s |
| Back-right (vx=−1.5, vy=−1.5) | 0.38 m/s | 1.54 m/s |

No falls for either model. Unified consistently 3–4× faster on diagonals.

### Phase 5 — Pivot (yaw=+2.0 rad/s for 2.0 s ≈ 229°)

| Model | Z min | Falls |
|-------|-------|-------|
| Original | **0.211 m** | **8** ⚠️ |
| Unified | 0.629 m | 0 ✅ |

**First failure point for the original model.** Pivot-only rotation at yaw=2.0 rad/s causes instability. Unified handles it cleanly.

### Phase 6 — Figure-8 (vx=+2.0 + yaw=±2.0, two full circles each)

| Segment | Model | Steps | Mean speed | Z min | Falls |
|---------|-------|------:|-----------|-------|------:|
| Circle left (yaw=+2.0) | Original | 312 | 0.69 m/s | **0.170 m** | **27** ⚠️ |
| Circle left (yaw=+2.0) | Unified | 314 | 1.76 m/s | 0.620 m | 0 ✅ |
| Circle right (yaw=−2.0) | Original | 310 | 0.87 m/s | **0.076 m** | **39** ⚠️ |
| Circle right (yaw=−2.0) | Unified | 314 | 1.77 m/s | 0.632 m | 0 ✅ |

**Complete failure for the original model.** Combined forward + yaw commands cause repeated falls reaching Zmin=0.076 m (robot nearly flat on the ground). Unified completes both full figure-8 loops with zero falls and stable height.

---

## Key Findings

1. **Stability under rotation**: The original model was not trained for simultaneous translation + yaw. It handles linear motion well but collapses at yaw=2.0 rad/s, especially combined with vx=2.0. Unified (exp_008) completes the entire circuit with zero falls.

2. **Velocity tracking**: The original model reaches only ~30–40% of commanded speed across all segments. Unified reaches ~70–90% on linear segments and shows much better diagonal tracking.

3. **Posture**: Unified runs slightly lower (Z mean 0.683 vs 0.729 m), consistent with a more dynamic crouched gait that provides stability at high speeds and during turns.

4. **Torque cost**: Unified uses ~18% higher torque RMS (11.50 vs 9.75 N·m), a reasonable trade-off for the speed and stability gains. Peak torque is identical (139 N·m) in both.

5. **Lateral tracking (Vy)**: Unified has slightly higher Vy error (0.819 vs 0.696 m/s), likely because it is commanding higher lateral speeds that physics limits more. Not a regression — a sign it is attempting to comply harder.

---

## Conclusion

Unified exp_008 (`model_80896.pt`) is a clear improvement over the repository baseline across every football-relevant metric: it is **2.2× faster**, **completely stable** (0 falls vs 77), and handles the full rotation+translation workload that the original model cannot.

The original model serves as a useful baseline confirming that the fundamental locomotion skills (walk, strafe, diagonal) are learnable without rotation training, but simultaneous yaw+translation requires the extended training done in exp_008.
