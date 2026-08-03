"""Testing ground: verify the PawPal scheduling logic end-to-end in the terminal."""

from pawpal_system import Owner, Pet, Task, Planner, Priority, Frequency
from rag_retriever import RAGRetriever

def main() -> None:
    # --- Create an owner and set their availability window ---
    owner = Owner(name="Amarachi", preferences="Morning person, prefers walks early")
    owner.set_available_time("07:00", "20:00")

    # --- Create at least two pets ---
    rex = Pet(name="Rex", species="Dog", age=4, health_notes="Needs joint supplement")
    luna = Pet(name="Luna", species="Cat", age=2)

    owner.add_pet(rex)
    owner.add_pet(luna)

    # --- Add tasks deliberately OUT OF ORDER (mixed times and priorities) ---
    # Added late in the day + low priority first...
    luna.add_task(Task(
        title="Litter box cleaning",
        category="Hygiene",
        duration_minutes=10,
        priority=Priority.LOW,
        preferred_time="12:00",
        frequency=Frequency.DAILY,
    ))
    # ...then a medium-priority evening task...
    rex.add_task(Task(
        title="Dinner",
        category="Feeding",
        duration_minutes=15,
        priority=Priority.MEDIUM,
        preferred_time="18:00",
        frequency=Frequency.DAILY,
    ))
    # ...then a high-priority late-morning task...
    luna.add_task(Task(
        title="Feed & fresh water",
        category="Feeding",
        duration_minutes=10,
        priority=Priority.HIGH,
        preferred_time="08:00",
        frequency=Frequency.DAILY,
    ))
    # ...and finally the earliest, high-priority task last.
    rex.add_task(Task(
        title="Morning walk",
        category="Exercise",
        duration_minutes=30,
        priority=Priority.HIGH,
        preferred_time="07:30",
        frequency=Frequency.DAILY,
    ))

    # --- Add TWO TASKS AT THE SAME TIME to exercise conflict detection ---
    # Both are scheduled for 09:00 but for different pets, so the single
    # owner can't do both at once -> the Planner should warn about the clash.
    rex.add_task(Task(
        title="Vet appointment",
        category="Health",
        duration_minutes=30,
        priority=Priority.HIGH,
        preferred_time="09:00",
        frequency=Frequency.ONCE,
    ))
    luna.add_task(Task(
        title="Grooming",
        category="Hygiene",
        duration_minutes=30,
        priority=Priority.MEDIUM,
        preferred_time="09:00",
        frequency=Frequency.DAILY,
    ))

    planner = Planner(owner=owner)

    # --- Show the tasks in the (unsorted) order they were added ---
    planner.collect_tasks()
    print("=" * 40)
    print("TASKS AS ADDED (out of order)")
    print("=" * 40)
    for task in planner.tasks:
        pet_name = task.pet.name if task.pet else "?"
        print(
            f"{task.preferred_time} — {task.title} "
            f"[pet: {pet_name}, priority: {task.priority.name.lower()}]"
        )

    # --- Demonstrate sort_tasks(): priority first, then preferred time ---
    planner.sort_tasks()
    print()
    print("=" * 40)
    print("AFTER sort_tasks() (priority, then time)")
    print("=" * 40)
    for task in planner.tasks:
        pet_name = task.pet.name if task.pet else "?"
        print(
            f"{task.preferred_time} — {task.title} "
            f"[pet: {pet_name}, priority: {task.priority.name.lower()}]"
        )

    # --- Demonstrate filter_tasks(): narrow down by pet ---
    print()
    print("=" * 40)
    print("AFTER filter_tasks(pet_name='Luna')")
    print("=" * 40)
    for task in planner.filter_tasks(pet_name="Luna"):
        print(f"{task.preferred_time} — {task.title}")

    # --- Demonstrate filter_tasks(): only incomplete tasks ---
    print()
    print("=" * 40)
    print("AFTER filter_tasks(completed=False)")
    print("=" * 40)
    for task in planner.filter_tasks(completed=False):
        print(f"{task.preferred_time} — {task.title}")

    # --- Demonstrate check_conflicts(): lightweight, warning-only check ---
    print()
    print("=" * 40)
    print("SCHEDULING CONFLICTS (check_conflicts())")
    print("=" * 40)
    print(planner.check_conflicts())

    # --- Build the plan and print Today's Schedule ---
    plan = planner.generate_plan()

    print()
    print("=" * 40)
    print("TODAY'S SCHEDULE")
    print("=" * 40)
    for item in plan:
        print(item)
    print("=" * 40)

    # Plain-language explanation from the planner as a bonus sanity check.
    print()
    print(planner.explain_plan())

    # --- Demonstrate generate_plan_with_context(): plan enriched with RAG tips ---
    retriever = RAGRetriever(knowledge_dir="knowledge")
    print()
    print("=" * 40)
    print("PLAN WITH CONTEXTUAL GUIDANCE (RAG)")
    print("=" * 40)
    print(planner.generate_plan_with_context(retriever))


if __name__ == "__main__":
    main()
