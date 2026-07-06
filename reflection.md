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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
