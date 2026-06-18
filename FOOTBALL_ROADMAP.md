# G1 Football — Robot Learning Roadmap with Closed Loop

> Architecture and executable plan. Hardware: RTX 4070 12GB, MuJoCo Warp, Holosoma, Unitree G1 29DOF.
> Current state: locomotion trained (reward 35.2, tracking 0.91), unified locomotion in progress.

---

## 1. Overview

### What we are building

A **policy iterative improvement system** where the train→evaluate→adjust loop
runs with minimal human intervention. The human defines objectives and approves changes;
the machines train, measure, criticise and propose.

```
Human defines target skill
   └→ Sonnet-planner generates experiment (config + rewards within allowed ranges)
       └→ Holosoma trains (MuJoCo Warp, hours)
           └→ Eval harness: rollouts + video + physical metrics
               └→ SigLIP scorer (fast, cheap) + VLM coach (qualitative)
                   └→ Sonnet-validator + Deterministic judge
                       └→ ACCEPT (promote checkpoint) / REJECT / PROPOSE changes
                           └→ back to start
```

### Why this is useful

- **The real bottleneck is human evaluation**: watching rollout videos and deciding
  "the walk looks off, raise the orientation penalty" consumes your time. That is automatable.
- **Physical logs are the ground truth; video is the context.** Metrics say *how much*,
  video says *why* (drags feet, crosses legs, leans).
- **Iterative reward shaping is the dominant task** in locomotion/skills RL. A semi-automatic
  loop multiplies the experiments per night.

### Automatic vs. human review

| Automatic | Requires human review |
|---|---|
| Launch training with validated config | Changes to torque/effort/velocity limits |
| Eval + video + metrics | Changes to safety termination conditions |
| SigLIP scoring + VLM critique | Any real-robot deployment |
| Reward weight proposals **within allowed ranges** | New rewards (new function, not just weight) |
| Checkpoint promotion if judge passes | Changes to the judge itself/allowed ranges |
| Experiment registry | Phase completion sign-off |

---

## 2. Technical architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR (python script + state on disk)                │
│  experiments/  ← JSON registry per experiment               │
│  checkpoints/  ← promoted, with metadata                    │
└──────┬───────────────────────────────────────────────────────┘
       │
  ┌────┴─────┐   ┌──────────┐   ┌───────────────┐
  │ TRAINER  │→  │ EVALUATOR │→  │ CRITIC STACK  │
  │ holosoma │   │ rollouts  │   │ SigLIP → VLM  │
  │ mjwarp   │   │ video     │   │ → Sonnet-val  │
  └──────────┘   │ metrics   │   └──────┬────────┘
                 └──────────┘          │
                              ┌────────┴────────┐
                              │ DETERMINISTIC    │
                              │ JUDGE (pure      │
                              │ python, no LLM)  │
                              └─────────────────┘
```

### Data flow per experiment

1. **Input**: `experiment.json` (skill, base config, proposed deltas, iteration budget)
2. **Trainer**: `train_agent.py exp:<skill> simulator:mjwarp` → `.pt/.onnx` checkpoints + TFEvents
3. **Evaluator**:
   - N deterministic rollouts with fixed seeds (e.g. 32 episodes, commands on a grid)
   - Video: holosoma already has `logger.video` (640×360, h264) — enable in eval
   - Physical metrics: extracted from TFEvents + own eval metrics (achieved velocity,
     falls, peak torques, gait symmetry, flight time)
4. **SigLIP scorer**: frame embeddings vs reference prompts ("humanoid robot running
   naturally" vs "robot falling" vs "robot dragging feet") → score per clip. Runs in seconds.
5. **VLM coach** (local Qwen2.5-VL): analyses 1-3 worst and 1 best clip → structured JSON
   with qualitative diagnosis.
6. **Hypothesis generator** (Sonnet): metrics + VLM critique + objective → structured
   change proposal (JSON, only allowed fields, within ranges).
7. **Validator** (Sonnet 2nd instance): reviews proposal against history — already tried?
   Contradicts a previous result? Risk of reward hacking?
8. **Deterministic judge** (python, no LLM): applies hard rules — ranges, minimum metrics,
   regressions. Final word.
9. **Registry**: everything to `experiments/<id>/` — config, metrics, scores, decision, video.

### Why the judge is deterministic

The LLM proposes, the code decides. The judge is a python script that validates:
- All fields in the proposal are in `allowed_ranges.json`
- New checkpoint metrics ≥ baseline on protected metrics
- No NaN/explosions in training

If the judge fails, there is no promotion — regardless of what the LLMs say.

---

## 3. Roadmap by phase

| Phase | Skill | New vs. current state | Estimate | Type |
|---|---|---|---|---|
| 0 | Infra: eval harness, video, registry | All tooling | 1-2 weeks | **MVP** |
| 1 | Robust locomotion (done) + unified (in progress) | Consolidate | in progress | **MVP** |
| 2 | Goal-oriented navigation (go to XY point) | New command: target position instead of velocity | 1 week | **MVP** |
| 3 | Approach the ball | Add ball to scene (rigid object), relative position obs | 1-2 weeks | **MVP** |
| 4 | Positioning to kick | Reward for ball-foot-goal relative pose | 2 weeks | Research |
| 5 | Static kick | Foot-ball contact, reward for ball velocity | 2-3 weeks | Research |
| 6 | Kick with approach | Compose phases 3+5, curriculum | 3 weeks | Research |
| 7 | Basic dribbling | Repeated contacts maintaining control | 4+ weeks | Research |
| 8 | 1v0 score goal | Compose everything, goal reward | 4+ weeks | Research |
| 9 | Simple 1v1 | Self-play, opponent | months | Future |
| 10 | Multi-skill agent | High-level planner over skills | months | Future |

**Key notes:**
- Phases 0-3 are the MVP for the first weeks. The ball in phase 3 uses
  `robot.object.object_urdf_path` / `scene.rigid_objects` which holosoma already supports.
- Phase 5 (kick) is the first real research leap: point contact with an object that
  bounces off is much harder than locomotion.
- DeepMind followed exactly this progression with OP3 (paper "Learning Agile Soccer Skills");
  worth replicating their decomposition: get-up, walk, kick, score → distill.

---

## 4. Skill library

### Hierarchy

```
HIGH-LEVEL (future)         football_planner (selects skill based on game state)
                                  │
MID-LEVEL (phases 3-8)      go_to_ball · align_to_kick · kick_moving · dribble
                                  │
LOW-LEVEL (phases 1-2)      stand · walk · run · turn_in_place · go_to_point
```

### Skill template (apply to each one)

```yaml
skill: go_to_point
objective: reach target XY position ±0.3m in <10s from 5m away
observations: [standard proprioceptive, relative_target_pos (2D), target_heading]
rewards:
  - tracking_position (exp decay over distance)    # new term
  - heading_alignment                               # new term
  - inherits locomotion penalties
success_metrics:
  - success_rate ≥ 90% on grid of 32 targets
  - mean time < 8s for targets at 5m
  - 0 falls in eval
common_failures:
  - orbiting the target without reaching it (insufficient reward shaping near goal)
  - late braking → overshoot
regression_tests:
  - standard locomotion eval still passes (don't forget walking)
  - eval of 32 targets with fixed seeds
promotion: passes judge with success_rate ≥ baseline and no regression in locomotion eval
```

Later-phase skills follow the same template; define them when reaching their phase,
not before (details will change based on what we learn).

---

## 5. Closed loop — exact definition

```
LOOP per experiment:
  1. INPUT: experiments/<id>/experiment.json
     {skill, parent_checkpoint, config_deltas, budget_iterations, eval_suite}
  2. TRAIN: train_agent.py with generated config → logs/<run>/
  3. AUTOMATED EVAL (when done or every N iters):
     a. 32 deterministic rollouts (fixed seeds, commands on a grid)
     b. video of 4 rollouts (best, worst, 2 random) — 10s each
     c. physical metrics → eval_metrics.json
  4. VISUAL SCORING (SigLIP, ~seconds):
     score per clip against positive/negative prompts → visual_scores.json
  5. MULTIMODAL CRITIQUE (Qwen2.5-VL, ~minutes):
     analyses extreme clips → coach_report.json (schema §8)
  6. PROPOSAL (Sonnet-planner):
     reads metrics + coach_report + history → change_proposal.json (schema §8)
  7. VALIDATION (Sonnet-validator):
     proposal already tried? contradicts history? hacking risk? → validation.json
  8. JUDGE (deterministic python):
     ranges + regressions + protected metrics → ACCEPT / REJECT
  9. IF ACCEPT: new child experiment.json, back to 2.
     IF REJECT: log reason, Sonnet-planner generates alternative (max 3 attempts,
     then escalate to human).
```

**Realistic cadence with our hardware**: 1 experiment of 25k iters ≈ 15h on the 4070.
The full loop yields ~1 iteration/day. Hence short budgets (5k iters, ~3h) for exploratory
experiments and 25k only for consolidation.

---

## 6. Harness engineering — contracts for BUILDING the system

> **Plane clarification.** Harnesses are NOT components of the training loop.
> They are the implementation contracts that allow LLM agents to build the system
> safely and verifiably. There are two planes:
>
> ```
> BUILD PLANE (multi-agent + harnesses)
>   Sonnet-planner → decomposes backlog into tasks with harness
>   Haiku → implements each task against its harness
>   Sonnet-validator → runs harness tests + adversarial review
>
>          ↓ builds ↓
>
> RUNTIME PLANE (normal software, the "product")
>   eval_rollouts.py · judge.py · registry · VLM coach · training loop
> ```

### Harness anatomy

A harness is the **executable specification of an implementation task**.
Written BEFORE implementing (the harness IS the test). Contains:

```
harnesses/H2_eval_rollouts/
├── SPEC.md           # purpose, context, constraints, what NOT to do
├── contract.json     # expected inputs/outputs, exact format
├── fixtures/         # test input data (small checkpoint, config)
├── test_harness.py   # tests the implementation MUST pass
└── acceptance.md     # verifiable criteria for the validator
```

Flow per task: **human/planner writes the harness → Haiku implements until
`test_harness.py` passes → Sonnet-validator reviews code + runs tests + looks for
shortcuts (did it hardcode the fixture?) → human merges.**

This inverts the usual model: instead of "Haiku writes code and then we see",
the success criterion exists before the code. Haiku cannot declare success —
the test declares it.

### The 10 initial harnesses (build the runtime deliverables)

| # | Harness | Deliverable it builds | Key harness tests | Implements | Validates |
|---|---|---|---|---|---|
| H1 | `H1_train_launcher` | train_agent.py wrapper with experiment.json | generated config == expected; aborts on NaN | Haiku | Sonnet-val |
| H2 | `H2_eval_rollouts` | eval_rollouts.py (32 deterministic episodes) | same seed → same metrics (bit-exact); JSON matches schema | Haiku | Sonnet-val |
| H3 | `H3_video_recorder` | clip recording in eval | valid mp4, correct duration, robot in frame | Haiku | Sonnet-val |
| H4 | `H4_metrics_extract` | extract_tfevents.py | key tags present; values == known fixture | Haiku | Sonnet-val |
| H5 | `H5_siglip_scorer` | visual scorer | scores in [0,1]; fall clip scores < good clip (fixture) | Haiku | Sonnet-val |
| H6 | `H6_vlm_coach` | Qwen2.5-VL invocation + parsing | output validates against schema; retries on invalid JSON | Haiku | Sonnet-val |
| H7 | `H7_proposer` | Sonnet invocation for change_proposal | every proposal passes range validation; rejects disallowed fields | Haiku | Sonnet-val |
| H8 | `H8_validator_agent` | critical Sonnet invocation | detects duplicate proposal from history (fixture) | Haiku | Sonnet-val |
| H9 | `H9_judge` | deterministic judge.py | exhaustive suite: ranges, regressions, edge cases; 100% coverage | Haiku | **Human** (it's the safety piece) |
| H10 | `H10_registry` | experiments/ + promotion | end-to-end traceable experiment with fixtures | Haiku | Sonnet-val |

Rule: if a Haiku implementation fails the harness 3 times, the task escalates to Sonnet
or the human — signal that the harness is mis-specified or the task is larger than estimated.

---

## 7. Agent roles

Agents operate on the **build plane**. In runtime only the embedded LLM invocations
remain (coach, proposer, proposal validator).

| Agent | Model | Plane | Responsibility | CANNOT |
|---|---|---|---|---|
| **Fable** (strategist) | Human + occasional Opus | build | Roadmap, write/approve harnesses, merge | — |
| **Planner** | Sonnet | build | decompose backlog into tasks with harness; write SPEC.md and tests | merge; modify approved harnesses |
| **Executor** | Haiku | build | implement against harness until tests pass | touch the harness; declare success (the test declares it) |
| **Validator** | Sonnet (separate instance) | build | adversarial review: shortcuts, fixture hardcoding, risks | approve H9 (judge) — that's human |
| **Proposer** | Sonnet (API, embedded) | runtime | change_proposal.json from metrics+coach | go outside allowed_ranges |
| **Proposal-critic** | Sonnet (API, embedded) | runtime | critique proposals vs. history | approve definitively |
| **VLM coach** | local Qwen2.5-VL-7B | runtime | diagnose clips | propose config changes |
| **SigLIP scorer** | local SigLIP | runtime | numerical score per clip | interpret |
| **Judge** | deterministic Python | runtime | final promotion decision | be modified without harness H9 + human review |

**Critical GPU constraint**: VLM and training compete for the 4070. Sequence: train →
unload VRAM → eval with VLM. The SigLIP scorer is small (~400MB) and can coexist.

---

## 8. Schemas and templates

### VLM coach prompt

```
You are a humanoid robot trainer. Watch this clip of a Unitree G1
executing the skill "{skill}". The objective was: {objective}.
Physical metrics for the episode: {metrics_summary}.

Reply ONLY with valid JSON according to this schema:
{schema}

Focus on: torso posture, step pattern, left/right symmetry,
foot contact, stability, and whether the behaviour seems natural or
exploits a shortcut (reward hacking).
```

### Evaluation schema (coach_report.json)

```json
{
  "clip_id": "string",
  "overall_quality": "1-5",
  "gait_assessment": {"symmetry": "1-5", "foot_clearance": "ok|dragging|excessive", "torso": "upright|leaning|unstable"},
  "failure_modes": ["string"],
  "reward_hacking_suspicion": {"detected": "bool", "description": "string|null"},
  "recommendation": "string (1-2 sentences)"
}
```

### Change proposal schema (change_proposal.json)

```json
{
  "experiment_parent": "exp_0042",
  "hypothesis": "string — what problem this addresses and why",
  "changes": [
    {"path": "reward.terms.feet_phase.params.swing_height", "from": 0.15, "to": 0.18}
  ],
  "expected_effect": {"metric": "Episode/rew_feet_phase", "direction": "up"},
  "budget_iterations": 5000,
  "abort_if": {"metric": "Train/mean_episode_length", "below": 200, "after_iteration": 3000}
}
```

### allowed_ranges.json (excerpt — the judge validates against this)

```json
{
  "reward.terms.tracking_lin_vel.weight": [0.5, 5.0],
  "reward.terms.feet_phase.params.swing_height": [0.05, 0.25],
  "command.lin_vel_x.max": [0.5, 4.0],
  "command.gait_period": [0.3, 1.5],
  "_human_only": [
    "robot.dof_effort_limit_list", "robot.control.*", "termination.*",
    "simulator.*", "allowed_ranges itself"
  ]
}
```

### Checkpoint promotion criteria

```json
{
  "protected_metrics": {
    "Train/mean_episode_length": {"min": 950},
    "eval.fall_rate": {"max": 0.05},
    "eval.success_rate": {"min_vs_baseline": 1.0}
  },
  "visual_gate": {"siglip_falling_score": {"max": 0.3}},
  "regression_suite": "locomotion_eval_v1 must pass",
  "human_signoff_required_for": ["phase_completion", "real_robot"]
}
```

---

## 9. Safety and limits

| Risk | Mitigation |
|---|---|
| **Torques/efforts** | `dof_effort_limit_list` and PD gains in `_human_only`. Judge rejects any proposal that touches them. |
| **Terminations** | Fall/contact conditions immutable by LLM — they are the training safety net. |
| **Real robot** | Out of scope for the loop. Deployment always manual, with checklist, after sim-to-sim eval in MuJoCo Classic. |
| **Dangerous rewards** | Validator explicitly looks for perverse incentives (e.g. ball velocity reward could incentivise stepping on it). Judge requires safety penalties never drop below a minimum floor. |
| **Visual overfitting** | SigLIP/VLM are never the sole gate — physical metrics rule. Visual score can only *veto* (detect bad), never *approve* alone. |
| **Reward hacking** | (1) explicit field in coach_report, (2) eval suite with conditions outside the training range, (3) protected metrics that cannot regress. |
| **Runaway loop** | Max 3 consecutive rejected proposals → escalate to human. GPU-hour budget per day. |

---

## 10. Final deliverable

### Initial backlog (20 tasks, execution order)

| # | Task | Phase | Type |
|---|---|---|---|
| 1 | `eval_rollouts.py` script: N deterministic episodes with seeds + JSON metrics | 0 | MVP |
| 2 | Enable `logger.video` in eval (already exists in holosoma config) | 0 | MVP |
| 3 | `extract_tfevents.py` script (almost done from previous analysis) | 0 | MVP |
| 4 | `experiments/` structure + experiment.json schema + registry | 0 | MVP |
| 5 | `allowed_ranges.json` v1 + judge script with tests | 0 | MVP |
| 6 | Install SigLIP locally + H5 harness with initial prompt set | 0 | MVP |
| 7 | Install Qwen2.5-VL-7B (GGUF/vLLM) + H6 harness | 0 | MVP |
| 8 | H7/H8 harnesses: planner and validator prompts + API invocation | 0 | MVP |
| 9 | Orchestrator v1: chain H1→H10 manually via CLI | 0 | MVP |
| 10 | Consolidate unified locomotion: eval exp_008 with the new harness | 1 | MVP |
| 11 | `locomotion_eval_v1` eval suite as permanent regression test | 1 | MVP |
| 12 | Design `go_to_point`: target position command term | 2 | MVP |
| 13 | Reward terms `tracking_position` + `heading_alignment` | 2 | MVP |
| 14 | Train go_to_point with warm-start from locomotion | 2 | MVP |
| 15 | First complete end-to-end closed loop on go_to_point | 2 | MVP |
| 16 | Add ball to scene (rigid object URDF) + relative position obs | 3 | MVP |
| 17 | Skill `go_to_ball` (go_to_point with target = ball) | 3 | MVP |
| 18 | Eval suite with ball in random positions | 3 | MVP |
| 19 | Design of `align_to_kick` (document, not code) | 4 | Research |
| 20 | Spike: foot-ball contact physics in MuJoCo Warp (is it stable?) | 5 | Research |

### First minimum viable experiment (this week)

**"Close the loop with what you already have":** use the current unified training run as the subject.
1. Backlog tasks 1-3 (eval + video + metrics) on `model_70897.onnx` from unified
2. SigLIP score of the clips (task 6)
3. One manual coach_report with Qwen2.5-VL (task 7)
4. Manual promotion decision following the criteria in §8

This validates each piece of the loop **without building the orchestrator yet**.

### Definition of "done" for the first demo

> The system executes a complete cycle without intervention: takes the unified checkpoint,
> evaluates it (32 rollouts + 4 videos), generates SigLIP scores and coach_report, Sonnet
> proposes a reward change within ranges, the validator reviews it, the judge accepts it,
> and the child experiment is automatically launched — all traced in `experiments/`.
> The human only reads the final summary.

---

## Appendix: deliberate design decisions

- **Physical logs > video**: video informs, metrics decide. Never the other way around.
- **Judge without LLM**: the only component with promotion authority is tested code.
- **Short budgets by default**: 5k exploratory iters, 25k for consolidation.
- **Warm-start whenever possible**: each skill starts from the parent checkpoint.
- **One GPU**: sequence training and VLM eval; don't try to parallelise.
- **Don't build phases 4+ yet**: their details will depend on what we learn in phases 0-3.
