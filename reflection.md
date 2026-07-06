# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

My initial UML design centered on four classes, each modeling one real-world entity or responsibility in the pet-care domain. I chose them so that data and behavior lived together, and so that no single class had to know too much about the others.


Owner: Represents the person using the app. It holds the owner's name, care preferences, and their available time window (availableStart / availableEnd). Its responsibility is managing the owner's own information and the relationship to their pets — adding a pet (addPet), updating preferences (updatePreferences), and setting the time window (setAvailableTime) that later constrains scheduling. An owner can own one or more pets.


Pet: Represents a single animal being cared for. It stores the pet's profile (name, species, age, healthNotes) and its list of careNeeds. Its responsibility is describing what care the pet requires — adding care needs (addCareNeed), updating the profile (updateProfile), and reporting the pet's daily requirements (getDailyRequirements). A pet has zero or more tasks.


Task: Represents one unit of care work, such as a walk or feeding. It captures the details a scheduler needs: title, category, durationMinutes, priority, preferredTime, and whether it's recurring. Its responsibility is knowing about itself — changing its own duration (updateDuration) or priority (changePriority), and answering scheduling questions like whether it's high priority (isHighPriority) or fits in the owner's available window (fitsInTimeWindow).


Planner: The coordinating class that ties everything together. It references an Owner, a Pet, and a list of Tasks, and its responsibility is turning those into an ordered daily plan. It generates the plan (generatePlan), sorts tasks by the planning rules (sortTasks), resolves overlapping or incompatible tasks (resolveConflicts), and produces a plain-language explanation of the result (explainPlan).


I separated the "data" classes (Owner, Pet, Task) from the "logic" class (Planner) on purpose: the first three describe the domain, while Planner owns all the scheduling decisions. This keeps the scheduling logic in one place and lets me change how plans are built without touching how pets or tasks are represented.

- What classes did you include, and what responsibilities did you assign to each?

Three core actions a user should be able to perform:
- A user should be able to add or update their pet's profile and the user's basic information.
- A user should be able to create and manage the pet's care tasks, like taking the pet on a walk at certain times in a day.
- A user should be able to not only view but create a daily care plan for their pet so that they can see their tasks for the day and their schedule.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

- Planner planned for one pet, but owners have many: 
Planner.pets: List[Pet]

- Tasks duplicated on Pet and Planner with no sync:
Pet.tasks is source of truth; Planner.collect_tasks() derives the working list

- Merged tasks couldn't say which pet they're for:
Task.pet back-reference, set by Pet.add_task()

- Times were strings (broken comparison/arithmetic):
parse_time() / format_time() ↔ minutes-since-midnight

- generate_plan returned a reordered list, not a schedule:
new PlanItem (task + start time); returns List[PlanItem]

- priority: str had no ordering:
Priority enum with rank

- recurring: bool can't say daily vs. weekly:
Frequency enum (ONCE/DAILY/WEEKLY)

- Nothing checked "time runs out":
Owner.available_minutes() capacity accessor


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers three main constraints. First, **priority**: each task carries a `Priority` enum (HIGH/MEDIUM/LOW) with an explicit numeric rank, and `sort_tasks()` orders by that rank first so urgent care (like medication) always claims a slot before optional care. Second, **time and duration**: every task has a `preferred_time` and a `duration_minutes`, and the owner has an availability window (`available_start`/`available_end`). The planner works in minutes-since-midnight so it can compare and arithmetic times reliably, place tasks without overlap, and drop a task entirely if it can't finish before the window closes. Third, **preferred time as a soft goal**: `generate_plan()` tries to honor each task's preferred start but treats it as a wish rather than a hard rule, sliding a task later when its ideal slot is already taken.

I decided priority mattered most because in pet care the real cost of a bad plan is skipping something important, not starting a walk ten minutes late — so the sort key is `(priority.rank, preferred_time)`, with priority as the primary key and time only as the tie-breaker. Availability came second because it's a hard physical limit (the owner genuinely isn't home outside the window), and preferred time came last because it's the constraint a person is most willing to bend.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff my scheduler makes is that generate_plan uses greedy, sequential packing that sacrifices a task's preferred time in order to guarantee a conflict-free plan. After sorting tasks by priority and then preferred start time, it walks the list once, tracking the earliest free minute (next_free). Each task is placed at start = max(preferred_time, next_free) — so whenever a task's preferred time has already been claimed by an earlier task, it is silently pushed to start right after the previous one ends rather than at the time the owner actually wanted. If pushing it past the end of the owner's availability window, the task is dropped from the plan entirely (continue).

This is reasonable for the pet-care scenario for a few reasons. First, it's predictable and easy to explain to the owner: tasks never overlap, and higher-priority care (e.g., medication) always wins the earlier slot. Second, the algorithm is a single O(n log n) sort plus one linear pass — cheap and deterministic, with no backtracking or search. The cost is that it's not optimal: it never tries to reshuffle or compress durations to honor more preferred times, and it can drop a low-priority task at the end of a full day rather than negotiating a better arrangement. For a daily home pet-care routine — where the owner mostly wants a sane, non-conflicting order and clear priorities — "good and understandable" is worth more than "mathematically optimal," so the tradeoff is a sensible one.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI across three distinct phases. During **design**, I used it as a brainstorming partner to pressure-test my UML — asking whether splitting the "data" classes (Owner, Pet, Task) from the "logic" class (Planner) was sound, and where my responsibilities were leaking across classes. During **implementation**, I leaned on it for refactoring: it was especially effective at translating my fragile string-based times into a clean minutes-since-midnight model (`parse_time`/`format_time`) and at proposing the `Priority` and `Frequency` enums that replaced my original `str`/`bool` fields. During **debugging and testing**, I used it to enumerate edge cases I hadn't thought of — touching-end-to-end intervals, tasks with no preferred time, a planner with no owner.

The most effective feature was **inline code generation with full-file context**: because the assistant could see the whole `pawpal_system.py`, its suggestions matched my existing naming and dataclass style instead of inventing new conventions. The most helpful *prompts* were narrow and grounded — "given this `generate_plan`, what breaks when two tasks share a preferred time?" produced far better answers than open-ended "write me a scheduler." Asking "why" questions ("why is a half-open interval the right overlap check?") turned the tool into something I learned from rather than just copied.

Using **separate chat sessions for each phase** kept me organized in a concrete way: my design session stayed focused on class responsibilities and never got polluted by stack traces, my implementation session held the evolving code and refactor history, and my testing session concentrated on edge cases and assertions. When I hit a bug I could open the right session with its context already loaded instead of scrolling past unrelated conversation, and it stopped the assistant from "helpfully" redesigning classes while I was only trying to fix a test.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

At one point the assistant suggested letting the `Planner` hold its own copy of tasks and mutate them directly — effectively duplicating task state on both `Pet` and `Planner`. I rejected that because it would have created two sources of truth that could silently drift apart. Instead I kept `Pet.tasks` as the single source of truth and had the planner *derive* its working list through `collect_tasks()`, which reads `owner.pets` and calls `owner.all_tasks()`. I made a similar call on the overlap check: an early suggestion used closed intervals, which would have flagged two tasks that merely abut (08:00–08:10 and 08:10–08:20) as a conflict; I changed it to half-open intervals so touching tasks are allowed.

I verified suggestions three ways. I **traced the data flow by hand** for the source-of-truth question — walking through what happens when a task is added via the Streamlit form and confirming the planner would still see it. I **wrote tests to pin the behavior**: `test_touching_end_to_end_is_not_a_conflict` and `test_two_tasks_at_exact_same_time_conflict` exist precisely because I wanted the interval logic proven, not assumed. And I **ran the app end-to-end**, adding real conflicting tasks and checking that the schedule came out non-overlapping and the explanation read sensibly. If a suggestion couldn't survive a test I'd written, I didn't keep it.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I organized the suite into three layers. **Data-model basics** confirm the building blocks behave: `mark_complete()` flips a task's status, `add_task()` increases a pet's task count and wires the `.pet` back-reference. **Core scheduling behavior** covers the three required capabilities — sorting correctness (equal-priority tasks come back chronologically, and priority beats an earlier low-priority task), recurrence logic (completing a DAILY task spawns tomorrow's copy, WEEKLY advances seven days, ONCE does not recur), and conflict detection. **Edge cases** cover the situations most likely to break in real use: two tasks at the exact same time, overlaps across different pets, a task with no preferred time, tasks that touch end-to-end, an empty plan, a task that overruns the availability window and gets dropped, filtering by completion and pet, a planner with no owner, and malformed time strings degrading to a warning instead of crashing.

These tests were important because the scheduler's value is entirely in its correctness under messy input — a pet owner will absolutely enter two 8:00 tasks or a walk that runs past bedtime. The edge-case layer in particular guards the exact assumptions I made in the algorithm (half-open intervals, greedy packing, window-based dropping), so if I later refactor `generate_plan`, the tests tell me immediately whether I preserved the promised behavior.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident the scheduler works correctly for the intended daily single-owner scenario. The behavior is deterministic (one sort plus one linear pass, no randomness), every branch in the conflict and planning logic has at least one test, and I've exercised it live through the Streamlit app. My confidence is highest on sorting and conflict detection and slightly lower on the greedy packing, since it's the part making the most tradeoffs.

If I had more time I'd test: tasks that cross midnight or have a preferred time outside the availability window; a large batch of tasks that exhausts the window to confirm exactly which low-priority ones get dropped and that the drop is stable; two tasks with identical priority *and* identical preferred time (tie-break stability); invalid or reversed availability windows (`end` before `start`); zero- or negative-duration tasks; and the recurrence chain over several days to make sure completed occurrences don't pile up and distort future plans.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the clean separation between the domain classes and the `Planner`. Keeping `Pet.tasks` as the single source of truth and having the planner derive its working list means the scheduling logic lives in exactly one place — I can change *how* plans are built without touching how pets or tasks are represented, and the Streamlit UI just hands over an `Owner` and trusts the planner. I'm also proud that the messy real-world details (string times, recurring chores, dropped-when-full tasks) are all handled explicitly rather than hidden, and that the conflict warnings surface in plain, owner-friendly language.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd upgrade the greedy scheduler. Right now it packs tasks sequentially and silently pushes or drops anything that doesn't fit, which is predictable but not clever — it never tries to honor more preferred times by reshuffling flexible tasks around fixed ones. In another iteration I'd separate "fixed-time" tasks (a vet appointment) from "flexible" tasks (a walk that can happen any time in the morning) and place the fixed ones first, then fit the flexible ones into the gaps. I'd also give the owner control over what happens when the day is over-full (which priorities to drop first) instead of it being an implicit side effect of sort order, and I'd validate time input at the edge so a bad string is caught before it reaches the planner.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The biggest thing I learned is what being the **lead architect** actually means when working with a powerful AI tool. The assistant is fast and often right about *local* details — a cleaner loop, a missing edge case, a better data type — but it doesn't own the shape of the system, and it will happily generate a plausible design that quietly violates a decision I'd already made (like duplicating task state across classes). My job was to hold the invariants: single source of truth, priority-first scheduling, logic isolated in the `Planner`. Once I stated those clearly, the AI became far more useful, because I could evaluate every suggestion against them and reject the ones that didn't fit. The tool accelerated the work, but the accountability for coherence, tradeoffs, and correctness stayed with me — I had to understand every line well enough to defend it in a test, not just accept it because it ran.
