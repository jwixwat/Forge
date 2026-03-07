# Adaptive Learning Controller Build Coordination

This document coordinates staged implementation of the closed-loop learning controller you described (factorized belief state + probe-family sensor models + residual separation + calibrated forecasting + exploration support + anchors/holdouts/adversarial + drift fixtures + DAG backchaining + anomaly/taxonomy governance + sim/OPE).

It is intentionally **non-technical**: no schemas, APIs, or code structure details appear here. Use it to align build order, dependencies, validation gates, and "don't-break" invariants over a long build.

Complexity key: **S** = contained, **M** = cross-cutting, **L** = heavy tuning/robustness.

---

## 1) Architectural README (compressed context)

### What this system does

Runs a session-based tutoring loop that **selects probes**, grades them (deterministic-first, LLM as untrusted helper), and updates a **versioned learner belief state** over:

* representation presence (absent/fragile/present)
* factorized misconceptions (mixture-capable)
* retention scheduling
* measurement/health residuals (model mismatch vs sensor unreliability vs spec ambiguity)

The system is hardened so beliefs remain **epistemically honest** in a closed loop by enforcing:

* **Predictive calibration** (beliefs must forecast next observations)
* **Measurement integrity** (anchors/shadow probes, holdout contamination protocols)
* **Non-invariance guards** (item weirdness + family health + item offsets)
* **Exploration support** (logged action probabilities)
* **Drift detection** (fixture sentinels; safe-mode degradation)
* **Governed ontology evolution** (taxonomy changes must improve predictive performance/transfer)

### Where it fits

A content-agnostic **CLI tutoring engine** consuming versioned content IR produced by a compiler pipeline. The loop must remain stable under spec evolution, grader drift, and policy iteration.

### Key mechanisms (must remain intact)

* **Belief as forecasting engine**: posterior must predict future measurement outcomes; monitored with proper scoring rules.
* **Evidence channels**: anchor / measurement / learning / shadow; diagnosis only from closed-book channels A/B/D.
* **Residual separation with mechanical definitions**: `model mismatch` vs `sensor unreliable` vs `spec underdetermined`, with invariant routing behavior.
* **Probe-family sensor models**: explicit, testable likelihoods; factor-first inference substrate; leaf modes are compiled views.
* **Non-invariance layer**: "item weirdness" and item offsets prevent misattributing item defects to learner factors.
* **Exploration substrate**: action selection is stochastic with minimum entropy; full propensities logged.
* **Holdouts as consumables** + contamination index.
* **Sentinel fixtures** are fixed inputs (CI + runtime self-tests), not learner items.
* **Anchors** are privileged, quota-enforced, cross-grader.
* **DAG backchaining is audited** (edge uncertainty, counterfactual tests).
* **Anomaly lifecycle** drives taxonomy updates; promotion requires predictive/transfer improvements.
* **Sim harness is adversarially mis-specified + fuzzed**; used as regression harness, not proof.
* **Versioned semantics + capped migrations** to avoid time-traveling learners.

### Core constraints / invariants (non-negotiable)

* **Deterministic-first grading**; LLM is an untrusted helper with injection hardening and versioning.
* **Closed-book diagnosis only**: tool-assisted/open-book cannot update factor diagnosis.
* **Posterior predictive checks always-on**: if miscalibrated, system must downgrade belief and enter safe mode.
* **Support for offline evaluation is structural**: action distributions must be sampled and logged (not optional).
* **Holdout integrity is preserved**: exposure is tracked; items retire/rotate; feedback delayed.
* **Sentinel drift monitoring uses fixtures**, not learner performance.
* **Spec ambiguity never punishes the learner**: underdetermined items are quarantined.
* **Controller cannot optimize belief stability**: anchor quotas and belief audits are enforced constraints.

### Invariants checklist (merge-gating)

| Invariant                                | Category      | How we verify                                                                                                   |
| ---------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------- |
| Deterministic-first grading              | Semantic      | For every attempt: deterministic rubric run when available; LLM use is explicit + versioned.                    |
| Closed-book gating for diagnosis         | Semantic      | Any diagnosis update traceable to closed-book evidence channels A/B/D only.                                     |
| Residuals are mechanical, not vibes      | Semantic      | Residual values recomputable from logged signals; routing invariants triggered deterministically.               |
| Posterior predictive checks run + logged | Epistemic     | Log/Brier (or equivalent) updated; miscalibration triggers safe mode.                                           |
| Exploration support exists               | Epistemic/Ops | Each selection logs candidate set + probability of chosen action; entropy floor enforced.                       |
| Sentinel fixtures pass                   | Ops           | CI fixture suite passes; runtime periodic self-test produces drift status.                                      |
| Holdout contamination tracked            | Epistemic     | Exposure counts, contamination index, retire/rotate behavior present and consistent.                            |
| Anchor quotas enforced                   | Epistemic     | Anchor sampling meets minimum quotas; belief audit computed; discrepancies recorded.                            |
| Non-invariance guardrails active         | Epistemic     | Item weirdness + family health computed; quarantine events logged.                                              |
| Versioned semantics                      | Ops/Semantic  | Every attempt/state update links content IR version + grader/prompt version + sensor model version.             |
| Safe mode degrades predictably           | Safety/Ops    | When drift/miscalibration triggers, allowed formats narrow, inference weight reduces, anchors/shadows increase. |

### Semantic contract (dangerous fields)

* **"Mastery/readiness"** is *not truth*; it's a decision statistic. Must be anchored and calibrated.
* **Factor posteriors** are *forecasting parameters*, not ground truth about cognition.
* **Leaf modes** are *UI views* only; must never become the inference substrate.
* **Shortcut resistance score** is a *guardrail*, not an optimization target.
* **Calibration alarms** are system health, not learner deficit.
* **Holdout scores** must be interpreted with contamination index; rising score can be practice effect.
* **Edge blocking probabilities** are hypotheses, must be audited and reversible.

### Anti-goals

* Not a "flashcard app" with pretty UI and ungrounded mastery bars.
* Not a deterministic curriculum that "feels smart" but has no support for offline evaluation.
* Not a system that diagnoses based on open-book or tool-assisted performance without explicit semantics.
* Not a taxonomy that grows without proving predictive/transfer value.

---

## 2) Dependency-ordered build plan by stage

### Stage v0 - Epistemic Spine + First Vertical Slice (end-to-end loop you can trust)

**Goal:** run complete sessions with reliable logging, deterministic grading, evidence channels, basic belief updates, and drift fixtures-before sophisticated control.

Execution order in Stage `v0` is now intentional rather than numeric. Version labels preserve
semantic lineage; the section order below reflects current implementation priority.

#### Risk register (v0)

* Risk: "we can run a session" but logs aren't rich enough to support calibration/OPE later.
  Mitigation: bake propensities + grading signals + evidence channels in from day 1.
* Risk: early LLM integration silently drives grading.
  Mitigation: deterministic-first invariant + fixture sentinels + explicit LLM versioning.

#### V0.0 Invariants charter + safety switches

* [x] Publish invariants checklist (above) as merge-gating criteria. *(spec complete in `docs/v0.0`)*
* [x] Define safe-mode behaviors (format restriction, inference weight reduction, increased anchors/shadows). *(spec complete in `docs/v0.0`)*
* [x] Define release discipline: every run is linked to versions (content + grader + sensor model). *(spec complete in `docs/v0.0`)*
* Acceptance: a "panic switch" exists and produces predictable degraded behavior.
* Complexity: **S/M**.

#### V0.1 Attempt ledger + state persistence spine

* [x] Persist attempt records with: item identity, evidence channel, assistance mode, grading signals, residual inputs, chosen action probability.
* [x] Persist learner state snapshots with version pointers.
* [x] Ensure idempotent session replays (no duplicate attempts or double-updates).
* Acceptance: full replay from logs reproduces state transitions (within deterministic tolerances).
* Complexity: **M**.

#### V0.2 Content IR ingestion + minimal domain slice (hand-built if needed)

* [x] Stand up a tiny domain: ~6 commitments in a prereq DAG. *(implemented in `content_ir/releases/content.v2026.03.04.regex.v0.2.json`)*
* [x] For each commitment: at least 1 measurement family + 1 teaching family (minimal). *(implemented in `content_ir/releases/content.v2026.03.04.regex.v0.2.json`)*
* [x] Include placeholders for holdouts/anchors/adversarial/shadow even if not active yet. *(forms + tags + adversarial generator/family placeholders in v0.2 bundle)*
* Acceptance: engine can load content IR and render items without engine code changes.
* Complexity: **M**.

#### V0.3 Deterministic grading + observation extraction

* [x] Score slot-based and MCQ formats deterministically where possible.
* [x] Produce observation patterns (slot pass/partial/fail + latency + hint usage).
* [x] Track rubric ambiguity counts (how many scoring paths fit).
* Acceptance: deterministic scoring is stable; ambiguous cases are flagged (not silently graded).
* Complexity: **M**.

#### V0.4 Residuals - mechanical computation + routing invariants (early!)

* [ ] Implement mechanical residual computations:

  * model mismatch from low likelihood under known hypotheses,
  * sensor unreliable from grader instability signals,
  * spec underdetermined from ambiguity signals.
* [ ] Enforce invariant routing:

  * spec underdetermined => quarantine (no learner penalty),
  * sensor unreliable => safe mode + structured formats,
  * model mismatch => anomaly queue.
* Acceptance: residuals are recomputable from logs; routing triggers are deterministic.
* Complexity: **M**.

#### V0.5 Sentinel fixtures (fixed inputs) - CI gate + runtime self-test

* [ ] Build fixture suite: correct/partial/incorrect/ambiguous/injection edge cases.
* [ ] Run in CI for grading pipeline changes; periodically in runtime as self-test.
* Acceptance: drift status is real and does not depend on learner behavior.
* Complexity: **M**.

#### V0.6 First belief update loop (simple but explicit)

* [ ] Maintain per-commitment state (representation + factors + basic retention placeholders).
* [ ] Use an explicit probe-family sensor model (even a small table) for updates.
* Acceptance: belief updates are explainable, testable, and don't depend on "LLM said so."
* Complexity: **M**.

#### V0.7 Feedback DSL execution + intervention logging

* [ ] Execute feedback moves via policy rules (hints/retry/contrast/worked example/etc.).
* [ ] Log feedback moves and hint levels as interventions (dose tracking begins now).
* Acceptance: feedback execution is content-agnostic and fully traceable in logs.
* Complexity: **M**.

#### V0.8 Sim harness skeleton (loop regression guard)

* [ ] Implement a minimal simulator loop with 3-4 archetypes and grader noise.
* [ ] Validate that routing doesn't thrash and residual routing works.
* Acceptance: basic regressions caught in sim before touching real users.
* Complexity: **M**.

#### V0.9 LLM parsing fallback (firewalled, explicit, optional; deferred until re-evaluated)

* [ ] LLM used only for parsing/classification when required; user text treated as data.
* [ ] Injection hardening and output validation are enforced.
* [ ] Multi-pass support exists for high-stakes contexts (even if disabled by default).
* Acceptance: LLM use is always logged and fixture-tested; deterministic-first still holds.
* Complexity: **M**.

---

### Stage v1 - Make Posteriors "Real": Predictive Calibration + Exploration Support + Non-Invariance Guards

**Goal:** beliefs become honest forecasts with calibration monitoring; policy decisions gain logged support; inference becomes robust to weird items.

#### Risk register (v1)

* Risk: beliefs look interpretable but aren't predictively calibrated.
  Mitigation: posterior predictive checks with proper scoring rules are always-on.
* Risk: offline evaluation is impossible because routing is deterministic.
  Mitigation: entropy floor + logged action distributions.

#### V1.0 Factor-first sensor model (leaf modes become views)

* [ ] Move inference substrate to factor-first likelihoods (even if simple/low-rank).
* [ ] Leaf modes exist only as compiled bundles for explanation/remediation.
* Acceptance: adding a leaf label cannot change inference unless factors change.
* Complexity: **M/L**.

#### V1.1 Posterior predictive checks (calibration layer)

* [ ] For each (commitment, probe family) produce predicted distribution over next observation patterns.
* [ ] Track log score/Brier (or equivalent) by strata (context, intervention, assistance mode).
* [ ] Trigger calibration alarms -> safe mode adjustments.
* Acceptance: system detects "beautiful but wrong" beliefs early, even before holdouts trend down.
* Complexity: **L**.

#### V1.2 Exploration substrate (support for OPE)

* [ ] Action selection becomes stochastic with minimum entropy constraint.
* [ ] Log candidate actions + probabilities for every selection.
* Acceptance: offline policy evaluation is structurally possible (support exists).
* Complexity: **M**.

#### V1.3 Non-invariance guardrails (item weirdness + offsets)

* [ ] Track "item weirdness" (surprise under predicted strength) and family health signals.
* [ ] Maintain a lightweight item difficulty offset that can be updated online.
* [ ] Quarantine items/families when weirdness accumulates.
* Acceptance: inference stops blaming learners for broken/shifted items.
* Complexity: **L**.

#### V1.4 Safe-mode policy (calibration-aware)

* [ ] Define graded safe mode levels based on drift and miscalibration.
* [ ] Safe mode constrains formats, increases anchors/shadows, reduces diagnosis update weight.
* Acceptance: miscalibration can't silently continue; system degrades predictably.
* Complexity: **M**.

#### V1.5 Sim harness expansion (calibration + invariance failures)

* [ ] Add mis-spec runs: within-family non-invariance, sudden insight, correlated factors.
* [ ] Verify calibration alarms and quarantine logic behave correctly.
* Acceptance: the harness catches your known failure classes, not just idealized cases.
* Complexity: **L**.

---

### Stage v2 - Measurement Integrity: Holdouts as Consumables, Anchors, Shadow Probes, Procedural Adversaries

**Goal:** independent measurement channels exist; contamination is tracked; anchor audits prevent controller Goodhart.

#### Risk register (v2)

* Risk: holdouts become training over time and "transfer" becomes a lie.
  Mitigation: consumable/parallel forms + delayed feedback + contamination index.
* Risk: drift monitoring confounds learner change.
  Mitigation: fixtures (already) + anchors cross-graded.

#### V2.0 Assistance modes contract (semantics preserved)

* [ ] Introduce explicit runtime assistance modes: closed-book / open-book / tool-assisted / mixed.
* [ ] Diagnosis updates only from closed-book evidence channels A/B/D.
* Acceptance: belief semantics remain meaningful even with external tools.
* Complexity: **M**.

#### V2.1 Holdout exams: forms + consumption + contamination protocol

* [ ] Build holdout forms (retire-on-use or rotate forms).
* [ ] Implement delayed feedback (teaching separated; holdout marked contaminated).
* [ ] Track contamination index and adjust interpretation of trends.
* Acceptance: holdout channel remains a usable audit signal over months.
* Complexity: **M/L**.

#### V2.2 Anchor channel: privileged audits + quotas + belief reconciliation

* [ ] Create anchor probes (fixed format, closed-book).
* [ ] Cross-grader evaluation (independent grading channel).
* [ ] Enforce anchor quotas and compute belief audit discrepancies.
* Acceptance: controller cannot game belief stability; anchors remain authoritative constraints.
* Complexity: **L**.

#### V2.3 Shadow probes (low contamination measurement)

* [ ] Add ultra-short, no-feedback probes with rotated formats.
* [ ] Use them for calibration and diagnosis checks.
* Acceptance: you can distinguish "learned from exposure" vs "measurement changed" better than weights alone.
* Complexity: **M**.

#### V2.4 Micro-randomization + pre/post measurement pairs

* [ ] Randomize between a small set of feedback moves in defined situations; log probabilities.
* [ ] After teaching moves, schedule post-measurement probes (ideally different family/format).
* Acceptance: you can estimate feedback primitive effects and reduce belief drift masquerading as learning.
* Complexity: **M/L**.

#### V2.5 Procedural adversarial generators + rotation + feedback-minimal

* [ ] Implement adversarial probe generation (minimal pairs/perturbations/counterexample prompts).
* [ ] Rotate and cap exposure; keep feedback minimal and/or batched.
* [ ] Track shortcut resistance as guardrail (constraint), not reward.
* Acceptance: adversarial measurement stays unlearned/unpredictable and remains diagnostic.
* Complexity: **M/L**.

---

### Stage v3 - Control Plane: Stable Routing + DAG Backchaining With Edge Audits

**Goal:** routing becomes stable and graph-aware; edges are treated as hypotheses and audited against counterfactual evidence.

#### Risk register (v3)

* Risk: DAG becomes a causal hallucination engine and reroutes upstream incorrectly.
  Mitigation: confirmatory probes + edge audits + counterfactual tests + edge uncertainty gating.
* Risk: control thrashes under uncertainty.
  Mitigation: plan blocks, hysteresis, switching costs, calibration-aware damping.

#### V3.0 Local router action set + damping

* [ ] Implement the full action set: introduce/prime, measure, remediate, discriminate, backchain, anti-shortcut, depth audit, certify, defer.
* [ ] Add plan blocks + hysteresis + switching costs.
* Acceptance: routing is stable and doesn't chase the last item.
* Complexity: **M/L**.

#### V3.1 Portfolio controller: constraint-first planning under intent

* [ ] Enforce floors/quotas: maintenance, anchors, shadows, holdouts, adversarial, exploration entropy, audits.
* [ ] Optimize remaining budget by value terms (forgetting risk, diagnosis value, coverage deficits, switching cost).
* [ ] Treat intent as constraint + debt accounting (not override chaos).
* Acceptance: controller remains aligned to long-horizon necessities under user intent.
* Complexity: **L**.

#### V3.2 DAG backchaining with confirmatory prereq probes

* [ ] Maintain probabilistic prereq blocking hypotheses.
* [ ] Never reroute upstream based on DAG priors alone-always confirm with prereq probes.
* [ ] Allow "top-down bridges" with limited credit (domain-dependent).
* Acceptance: prereq routing is evidence-based, not structure-based.
* Complexity: **M/L**.

#### V3.3 Edge audit protocol + counterfactual backchaining tests

* [ ] Track per-edge audit statistics ("downstream improves despite prereq fail?").
* [ ] Run randomized counterfactual tests when prereq fails (sometimes remediate downstream anyway).
* [ ] Update edge blocking strength and edge uncertainty over time.
* Acceptance: false upstream reroutes decrease; DAG becomes empirically grounded.
* Complexity: **L**.

#### V3.4 Coverage gates: contexts, factors, and integration discipline

* [ ] Track coverage of authored contexts + core factors probed/cleared.
* [ ] Keep integration items certification-first unless decomposed; prevent credit assignment traps.
* Acceptance: coverage reflects transferable competence, not tag-count illusions.
* Complexity: **M**.

---

### Stage v4 - Content Compiler + Governance: Spec Corruption Defense, Anomaly Lifecycle, Taxonomy Evolution, Migrations

**Goal:** robust content pipeline produces trustworthy IR; ontology evolves only when it improves predictions/transfer; state migrations are safe and capped.

#### Risk register (v4)

* Risk: spec corruption (wrong keys/rubrics) creates "truth drift" that evaluation can't detect.
  Mitigation: multi-source generation + property tests + runtime anomaly detectors.
* Risk: taxonomy bloat returns via leaf modes.
  Mitigation: factor-first inference + promotion gates tied to predictive calibration/transfer.

#### V4.0 Compiler pipeline (source specs -> versioned IR)

* [ ] Implement end-to-end compilation: items, rubrics, feedback policies, sensor priors, holdouts, anchors, fixtures, adversarial generators.
* [ ] Enforce versioned outputs with migration metadata.
* Acceptance: engine consumes IR without domain-specific runtime changes.
* Complexity: **M/L**.

#### V4.1 Family invariance & discriminability validation

* [ ] Enforce invariance contracts within families; reject "garbage bucket" families.
* [ ] Compute discriminability proxies (e.g., MI estimates) and require minimum thresholds.
* Acceptance: probes are actually identifiable instruments, not just question piles.
* Complexity: **L**.

#### V4.2 Spec corruption defenses (compiler-time)

* [ ] Independent generation + disagreement resolution for keys/rubrics/discriminators.
* [ ] Property-based tests where executable semantics exist; otherwise structured adversarial checks.
* Acceptance: wrong rubrics are caught before they become "truth."
* Complexity: **L**.

#### V4.3 Runtime spec anomaly detectors + quarantine workflows

* [ ] Detect items/families failing unexpectedly relative to anchors/holdouts and predicted strength.
* [ ] Quarantine aggressively; tag content defects separately from learner deficits.
* Acceptance: spec defects don't silently poison learning and diagnosis.
* Complexity: **M**.

#### V4.4 Anomaly lifecycle: discovery -> proposal -> promotion gates

* [ ] Accumulate mismatch anomalies (not sensor/spec issues).
* [ ] Offline clustering and hypothesis proposal (new factor or new leaf bundle).
* [ ] Promotion requires improvements in predictive calibration and/or anchor/holdout transfer, replicated across families.
* Acceptance: taxonomy evolves only when it buys predictive power, not interpretive comfort.
* Complexity: **L**.

#### V4.5 Spec evolution & state migrations (versioned semantics)

* [ ] Immutable IDs + alias maps for merges.
* [ ] Optional regrading of old logs under new model.
* [ ] Capped re-estimation so schedules don't chaos-reset.
* Acceptance: no time-travel learner semantics; updates are explainable and reversible.
* Complexity: **L**.

---

### Stage v5 - Depth, Latent Contexts, Offline Policy Evaluation, Ops Maturity

**Goal:** depth audits are structured and safe; latent clusters are meaningful alerts; offline evaluation is usable; ops discipline prevents silent regressions.

#### Risk register (v5)

* Risk: depth audits become a Goodhart target ("learn to satisfy the grader's aesthetic").
  Mitigation: structured slots + deterministic checks + LLM coarse abstaining + tie weight to transfer.
* Risk: clustering tracks style not cognition.
  Mitigation: structural features + stability checks; clusters are alerts, not truth.

#### V5.0 Structured depth audits (low frequency, high value)

* [ ] Require structured explanation slots; deterministic consistency checks.
* [ ] LLM only coarse classify with abstention (coherent/incoherent/unclear).
* [ ] Automatically downweight audit credit if it doesn't predict transfer.
* Acceptance: depth audits add signal without becoming an easy gaming channel.
* Complexity: **M/L**.

#### V5.1 Latent context clustering on task structure + stability checks

* [ ] Cluster using structural features (schema topology, operation type, steps/bindings, distractor type).
* [ ] Test cluster stability under paraphrase; treat unstable clusters as weak signals.
* [ ] Use clusters as alerts triggering targeted probe generation.
* Acceptance: distribution shift detection becomes useful without hallucinating new contexts.
* Complexity: **M/L**.

#### V5.2 Offline policy evaluation toolkit (OPE)

* [ ] Use logged propensities to compare routing variants (with explicit support checks).
* [ ] Produce "policy deltas" reports with uncertainty bounds and failure modes highlighted.
* Acceptance: policy iteration is evidence-driven, not vibes-driven.
* Complexity: **L**.

#### V5.3 Calibration/health dashboards + release discipline

* [ ] Reporting for predictive calibration by family/channel/assistance mode.
* [ ] Reporting for drift fixture status, quarantine rates, anomaly rates, edge audit health, contamination-adjusted holdouts.
* [ ] Release checklist binds versioned semantics to CI fixture passes and sim regressions.
* Acceptance: operational changes can't silently degrade epistemic integrity.
* Complexity: **M**.

---

### Stage Full - Scale-out + Long-Run Governance

**Goal:** scale content and domains while preserving epistemic integrity; harden the system for years of iteration.

#### Full-1 Multi-domain scaling playbook

* [ ] Authoring guidelines for commitments/probe families/factors/feedback.
* [ ] QA gates and "reject reasons" for families (non-invariance, low discriminability, spec ambiguity).
* [ ] Content production economics: parallel forms for holdouts; procedural adversaries; anchor sets.
* Acceptance: scaling content doesn't collapse measurement integrity.
* Complexity: **L**.

#### Full-2 Human audit channel (optional but powerful)

* [ ] Interface for occasional human-graded anchor audits.
* [ ] Incorporate as privileged anchors without overusing (cost-aware quotas).
* Acceptance: "ground truth anchors" exist beyond your grader stack.
* Complexity: **M/L**.

#### Full-3 Model upgrades (only when they improve calibration/transfer)

* [ ] Upgrade sensor models (richer factor models, IRT-like components, better treatment-effect estimation).
* [ ] Every upgrade requires predictive calibration improvements on frozen logs + anchor/holdout benefit.
* Acceptance: sophistication increases honesty, not just complexity.
* Complexity: **L**.

#### Full-4 Governance: taxonomy growth discipline

* [ ] Rate-limit ontology changes; promotion gates enforced; deprecation policy via alias maps.
* [ ] Longitudinal monitoring of taxonomy growth, anomaly rates, and predictive fit.
* Acceptance: ontology doesn't bloat; semantics remain stable.
* Complexity: **M/L**.

---

## 3) Validation checkpoints (gates)

All gates are **prequential (forward-only)** and evaluated primarily on **anchors/shadows/holdouts** rather than self-confirming practice streams.

### Gate to v1 (after v0)

* [ ] End-to-end sessions run with idempotent attempt logging and state persistence.
* [ ] Deterministic-first grading enforced; LLM use is explicit and fixture-tested.
* [ ] Mechanical residuals computed and routing invariants enforced.
* [ ] Sentinel fixture suite exists in CI; runtime self-test produces drift status.
* [ ] Sim harness catches basic thrash and routing invariant violations.

### Gate to v2 (after v1)

* [ ] Posterior predictive checks operational (log/Brier tracked) with safe-mode triggers.
* [ ] Exploration substrate active: action probabilities logged with minimum entropy.
* [ ] Non-invariance guardrails active: item weirdness and quarantine events observable.

### Gate to v3 (after v2)

* [ ] Assistance modes enforced: diagnosis updates are closed-book only.
* [ ] Holdouts implemented as consumables/forms; contamination index tracked; feedback delayed.
* [ ] Anchor channel live: quotas enforced, cross-grader grading, belief audits computed.
* [ ] Shadow probes + pre/post measurement pairs + micro-randomized feedback in place.
* [ ] Procedural adversarial probes rotating; feedback-minimal; resistance treated as guardrail.

### Gate to v4 (after v3)

* [ ] Router stability: hysteresis + plan blocks prevents thrash; switching costs working.
* [ ] DAG backchaining evidence-based; edge audits reduce false upstream reroutes.
* [ ] Coverage gating for contexts/factors operational; integration items handled safely.
* [ ] Sim harness includes mis-spec + fuzzing; worst-case behavior acceptable.

### Gate to v5 / Full (after v4)

* [ ] Compiler produces versioned IR with invariance/discriminability/spec-corruption checks.
* [ ] Anomaly lifecycle produces candidate taxonomy updates; promotion gates based on calibration/transfer.
* [ ] Spec migrations are reversible and capped (no schedule chaos).
* [ ] Depth audits structured + safe; latent clusters stable and useful as alerts.
* [ ] Offline policy evaluation runs with support checks and uncertainty reporting.
* [ ] Ops dashboards and release discipline prevent silent regression.

---

## One ordering note (why this is the "fastest manifold")

The build order above deliberately front-loads the **epistemic spine** (logs, residual invariants, fixtures, deterministic-first) and the **truth-maintenance layer** (predictive calibration, exploration support, non-invariance guards) *before* sophisticated control and content scaling. That prevents rework and avoids building a high-velocity curriculum engine atop un-auditable measurement.
