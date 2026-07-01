# Training Proposal: Football-Circuit-Guided Locomotion

**Status:** Draft — open questions to discuss with team
**Date:** 2026-07-01

---

## Motivation

Evaluation of `ppo_g1_29dof.onnx` (repo baseline) vs `model_80896.pt` (exp_008) on the football
circuit revealed a clear failure mode: the baseline collapses at `yaw=±2.0 rad/s`, especially
combined with `vx=2.0`. Root cause: current training command ranges cap yaw at ±1.0 rad/s —
the robot never saw the hard combinations during training.

Goal: train a model that is **stable across a wide range of movements**, using the football
circuit as the training distribution and a separate validation circuit to measure generalization.

---

## Core Idea

1. **Train** on a command distribution derived from the football circuit (covers the hard combinations)
2. **Validate** on a different circuit the model has never seen
3. Use **cross-track error** (distance from the ideal path) as an eval metric — not as a training
   reward, to avoid sim-to-real gap from global position dependence

---

## Open Design Questions

### Q1 — How to use the football circuit in training?

**Option A — Expand command ranges**
Simply widen the uniform sampling to cover football demands:
- `lin_vel_x`: [-1.5, 2.5]
- `lin_vel_y`: [-2.0, 2.0]
- `ang_vel_yaw`: [-2.0, 2.0]

Pro: minimal change, builds on existing infrastructure.
Con: samples the full space uniformly — hard combinations (vx=2 + yaw=2) are rare by chance.

**Option B — Sample from circuit segments**
Treat each football circuit segment as a command "mode" and sample from them with weights.
Modes would include: sprint, strafe, retreat, diagonal, pivot, figure-8.

Pro: explicitly exposes the model to the hard combinations.
Con: more complex, less generalisation pressure from unseen combinations.

**Decision needed:** A, B, or a mix (wide range + bias toward hard combinations)?

---

### Q2 — What should the validation circuit look like?

Needs to cover movements the football circuit does NOT have, to measure true generalisation.

Candidate movements to include:
- **Slalom** — high-speed zigzag with smooth curves (no abrupt stops)
- **Sprint + brake** — rapid acceleration then deceleration to zero
- **Slow sustained yaw** — low yaw held for long duration (different from football's fast pivot)
- **L-shape** — forward sprint → 90° walk → forward sprint (no strafe, no diagonal)
- **Backward sprint** — sustained high-speed retreat

**Decision needed:** which of these to include, and at what speeds?

---

### Q3 — Path tracking as eval metric (not reward)

Proposal: after each eval run, compute a **reference trajectory** by integrating the command
sequence (dead-reckoning), then measure:

- **Cross-track error** — perpendicular distance from robot to nearest point on the reference path
- **Along-track progress** — how far along the path the robot reached before falling or diverging

This gives a richer signal than "did it fall?" — a model that stays upright but drifts 3 m off
the intended route scores differently from one that tracks the path tightly.

Sim-to-real note: global position is available in sim, not on the real robot. Keeping this as a
**metric only** (not a reward term) avoids introducing a sim-to-real gap.

**Decision needed:** is cross-track error the right primary metric, or do we prefer speed-tracking
error as the main number?

---

### Q4 — Reward shaping

Current reward terms: `tracking_lin_vel`, `tracking_ang_vel`, `penalty_ang_vel_xy`,
`penalty_orientation`, `feet_phase`, `pose`, `alive`, `penalty_close_feet_xy`, `penalty_feet_ori`.

Candidates for modification:
- **Increase `tracking_ang_vel` weight** — the yaw tracking is clearly the bottleneck
- **Add height floor penalty** — penalise Z < 0.65 m heavily (currently only `alive` at Z~fall)
- **Velocity bonus** — reward absolute speed achieved, not just tracking error

**Decision needed:** which terms to tune first, and by how much?

---

### Q5 — Warm-start vs. train from scratch

- **Warm-start from `model_80896.pt`**: faster convergence, but may carry biases that limit improvement on yaw+translation
- **Train from scratch**: more freedom, higher compute cost

**Decision needed:** which starting point?

---

## Proposed Next Steps

1. Agree on answers to Q1–Q5 above
2. Design the validation circuit (new script in `loop/`)
3. Implement cross-track error metric in eval pipeline
4. Run a short training experiment with expanded command ranges (Q1-A) as a cheap baseline
5. Evaluate on both circuits and compare

---

## Reference

- Baseline eval: `experiments/EVAL_FOOTBALL_REPORT.md`
- Football circuit definition: `loop/eval_sequence.py::build_football_sequence()`
- Current command ranges: `src/holosoma/holosoma/config_values/loco/g1/command.py`
- Current reward terms: `src/holosoma/holosoma/config_values/loco/g1/reward.py`
