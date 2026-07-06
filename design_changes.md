# PawPal+ Design Change Proposal

This documents the revisions made to the class design before implementing scheduling
logic. Each change is motivated by a relationship gap or a logic bottleneck found while
reviewing the original skeleton against the UML and the README requirements.

## 1. Planner plans for all of an owner's pets

**Problem.** The UML declares `Owner "1" --> "1..*" Pet`, and `Owner` correctly holds a
list of pets, but `Planner` held a single `pet: Pet | None`. A multi-pet owner could
never get a combined plan.

**Change.** `Planner` now holds `pets: List[Pet]` (with `owner`). A single-pet owner is
just a list of length one.

## 2. One source of truth for tasks

**Problem.** Tasks lived on both `Pet.tasks` and `Planner.tasks` with no rule linking
them. The two lists could silently diverge, and it was unclear which one `generate_plan`
should read.

**Change.** `Pet.tasks` is the source of truth. `Planner.tasks` becomes a *derived*
working list, populated by a new `collect_tasks()` method that flattens the tasks off
every pet the planner is responsible for.

## 3. Tasks know which pet they belong to

**Problem.** Once tasks from several pets are merged into one plan, the output could not
say which pet a task ("Feeding") was for.

**Change.** `Task` gains an optional `pet` back-reference. `Pet.add_task()` sets it, so
the plan can attribute every item to a pet.

## 4. Real time representation

**Problem.** `available_start`, `available_end`, and `preferred_time` were all `str`.
String comparison is wrong (`"9:00" > "10:00"`), and you cannot add a duration to a
string. This blocks sorting, window-fitting, and conflict detection.

**Change.** Add module-level `parse_time()` / `format_time()` helpers that convert
between `"HH:MM"` strings (kept for UI/serialization) and integer minutes-since-midnight
(used for all arithmetic and comparison).

## 5. A plan is scheduled slots, not a reordered task list

**Problem.** `generate_plan()` returned `List[Task]`. A reordered list is not a
schedule; the README output (`08:00 — Morning walk`) needs an assigned start time per
task.

**Change.** Introduce a `PlanItem` dataclass (`task` + `start_minutes`). `generate_plan()`
now returns `List[PlanItem]`. Each item can compute its end time, which is what conflict
detection needs.

## 6. Priority is an ordered enum

**Problem.** `priority: str` made `sort_tasks()` and `is_high_priority()` guess valid
values and gave no defined ordering.

**Change.** Add a `Priority` enum (`HIGH`, `MEDIUM`, `LOW`) with an explicit rank so
sorting is deterministic.

## 7. Recurrence is expressible as daily vs. weekly

**Problem.** `recurring: bool` cannot express the README's "daily vs. weekly"
distinction.

**Change.** Replace `recurring: bool` with a `Frequency` enum (`ONCE`, `DAILY`,
`WEEKLY`).

## 8. Capacity / "time runs out" filtering has a home

**Problem.** The README calls for skipping tasks when time runs out, but nothing compared
available minutes against summed durations.

**Change.** Add `Owner.available_minutes()` (window length) and note that
`generate_plan()` is responsible for dropping/deferring tasks that exceed capacity. The
filtering itself is left as implementation work.

## What stays as stubs

The scheduling *algorithms* — `generate_plan`, `sort_tasks`, `resolve_conflicts`,
`explain_plan`, and `Task.fits_in_time_window` — keep placeholder bodies with the
updated signatures. Only the structural design, the type-conversion helpers, and the
trivially-determined accessors are implemented here.
