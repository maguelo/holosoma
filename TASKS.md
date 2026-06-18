# Tasks

## 🔴 Pending

- [ ] **Launch exp_009** — `make train-unified3`
  - Fixes forward lean at sprint: `penalty_orientation -20` (was -10) + `base_height -3.0` (desired 0.89m)
  - Warm-start from `model_80896.pt` (exp_008)
  - Run for 10k iterations, monitor `logs/train_unified3.log`

## 🟡 In progress

_(nothing currently running)_

## 🟢 Done

- [x] exp_001 — walking baseline (model_24999.pt)
- [x] exp_002 — jog/trot ≤1.0 m/s (model_35900.pt)
- [x] exp_003 — lateral strafe goalkeeper (model_34998.pt)
- [x] exp_004 — sprint stage 1, 52° yaw drift (model_45899.pt)
- [x] exp_005 — sprint stage 2, discarded (jog-in-place local optimum)
- [x] exp_006 — sprint stage 3, 1.73 m/s real, 82% aerial (model_55898.pt)
- [x] exp_007 — unified locomotion: backwards + turns + sprint (model_70897.pt)
- [x] exp_008 — unified stage 2: narrow gait, sprint still unstable (model_80896.pt)
- [x] Scripted eval circuits: `loop/eval_sequence.py` (basic + football)
- [x] Comparative eval: walking vs unified — direction confirmed correct

## 🔵 Backlog

- [ ] After exp_009: run `make eval-football` with new checkpoint, check forward lean
- [ ] If diagonals freeze in football circuit: lower diagonal vx to 1.5 (vx+vy combined > 2.0 → out of distribution)
- [ ] exp_010 (if needed): train with explicit diagonal command ranges (vx+vy simultaneously sampled)
- [ ] Push all commits to origin: `git push`


# NOTES
Strafe is not stable, it is not fully horizontal 
strafe diagonal backward is not stable, is not simetric.