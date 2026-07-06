import streamlit as st

from pawpal_system import Owner, Pet, Task, Planner, Priority, Frequency, format_time

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# --- The Owner lives in the session "vault" so it persists across re-runs. ---
# Create it once; on every later re-run we reuse the same object (and the pets
# and tasks already attached to it).
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner = st.session_state.owner

st.subheader("Owner")
owner_name = st.text_input("Owner name", value=owner.name)
col_start, col_end = st.columns(2)
with col_start:
    available_start = st.text_input("Available from (HH:MM)", value=owner.available_start or "08:00")
with col_end:
    available_end = st.text_input("Available until (HH:MM)", value=owner.available_end or "20:00")
# Keep the persistent Owner in sync with the form each run.
owner.name = owner_name
owner.set_available_time(available_start, available_end)

st.divider()

# --- Adding a Pet: build a Pet, then hand it to Owner.add_pet(). ---
st.subheader("Add a Pet")
with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age (years)", min_value=0, max_value=40, value=2)
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    # Owner.add_pet() is the method that handles the submitted data.
    owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
    st.success(f"Added {pet_name}.")

if owner.pets:
    st.write("Current pets:")
    st.table(
        [{"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.tasks)} for p in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Scheduling a Task: build a Task, then Pet.add_task() attaches it. ---
st.subheader("Add a Task")
PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}

if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form"):
        pet_choice = st.selectbox("For which pet?", [p.name for p in owner.pets])
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.text_input("Category", value="exercise")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col2:
            preferred_time = st.text_input("Preferred time (HH:MM)", value="08:00")
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=1)
        add_task = st.form_submit_button("Add task")

    if add_task:
        task = Task(
            title=task_title,
            category=category,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority],
            preferred_time=preferred_time,
            frequency=Frequency(frequency),
        )
        # Find the chosen pet in the persistent owner, then attach the task.
        pet = next(p for p in owner.pets if p.name == pet_choice)
        pet.add_task(task)  # Pet.add_task() handles the submitted task data.
        st.success(f"Added '{task_title}' to {pet.name}.")

# Show every task currently attached to the owner's pets. We hand the owner
# to a Planner so the table reflects the Planner's own ordering (priority, then
# preferred time) and so we can surface any scheduling clashes up front.
task_planner = Planner(owner=owner)
task_planner.collect_tasks()
task_planner.sort_tasks()

if task_planner.tasks:
    # A best-effort conflict check that degrades to a warning instead of
    # crashing on bad time strings.
    conflict_message = task_planner.check_conflicts()
    if conflict_message.startswith("OK"):
        st.success(conflict_message)
    else:
        st.warning(conflict_message)

    st.write("Current tasks (in planning order):")

    # --- Filter controls: let the Planner do the filtering via filter_tasks(). ---
    filter_pet_col, filter_status_col = st.columns(2)
    with filter_pet_col:
        pet_filter = st.selectbox(
            "Filter by pet", ["All pets"] + [p.name for p in owner.pets]
        )
    with filter_status_col:
        status_filter = st.selectbox(
            "Filter by status", ["All", "To do", "Completed"]
        )

    # Translate the UI choices into filter_tasks() arguments.
    completed_arg = {"All": None, "To do": False, "Completed": True}[status_filter]
    pet_arg = None if pet_filter == "All pets" else pet_filter
    filtered_tasks = task_planner.filter_tasks(completed=completed_arg, pet_name=pet_arg)

    # Summary metrics give the filtered view a professional, at-a-glance header.
    total_minutes = sum(t.duration_minutes for t in filtered_tasks)
    high_priority = sum(1 for t in filtered_tasks if t.is_high_priority())
    metric_count, metric_time, metric_high = st.columns(3)
    metric_count.metric("Tasks shown", len(filtered_tasks))
    metric_time.metric("Total time", f"{total_minutes} min")
    metric_high.metric("High priority", high_priority)

    if filtered_tasks:
        st.table(
            [
                {
                    "pet": t.pet.name if t.pet else "?",
                    "title": t.title,
                    "duration_minutes": t.duration_minutes,
                    "priority": t.priority.name.lower(),
                    "preferred_time": t.preferred_time,
                    "status": "done" if t.completed else "to do",
                }
                for t in filtered_tasks
            ]
        )
    else:
        st.info("No tasks match the current filters.")

st.divider()

# --- Build Schedule: hand the Owner to a Planner and show its plan. ---
st.subheader("Build Schedule")
st.caption("Uses your Planner to order the tasks into a conflict-free daily plan.")

if st.button("Generate schedule"):
    planner = Planner(owner=owner)
    plan = planner.generate_plan()
    if not plan:
        st.warning("No tasks could be scheduled. Add tasks (and check the availability window).")
    else:
        st.success(f"Scheduled {len(plan)} task(s) into a conflict-free plan.")
        st.table(
            [
                {
                    "start": format_time(item.start_minutes),
                    "end": format_time(item.end_minutes),
                    "task": item.task.title,
                    "pet": item.task.pet.name if item.task.pet else "?",
                    "priority": item.task.priority.name.lower(),
                }
                for item in plan
            ]
        )
        st.markdown("**Explanation**")
        st.text(planner.explain_plan())

        # Surface any preferred-time clashes the Planner detected. The plan
        # above is already conflict-free (tasks get pushed later), but this
        # explains where the owner's original preferred times overlapped.
        st.markdown("**Conflict check**")
        st.text(planner.explain_conflicts())
