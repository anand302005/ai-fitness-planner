import json

import streamlit as st

from llm_client import generate_plan

st.set_page_config(
    page_title="AI Workout & Diet Planner",
    page_icon="💪",
    layout="wide",
)


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    if height_cm <= 0:
        return 0.0
    height_m = height_cm / 100.0
    return weight_kg / (height_m ** 2)


def estimate_calories(
    age: int,
    gender: str,
    weight_kg: float,
    height_cm: float,
    activity_level: str,
    goal: str,
) -> int:
    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity_factor = {
        "Sedentary": 1.2,
        "Lightly active": 1.375,
        "Moderately active": 1.55,
        "Very active": 1.725,
    }.get(activity_level, 1.2)

    maintenance = bmr * activity_factor

    if goal == "Weight loss":
        target = maintenance - 300
    elif goal == "Muscle gain":
        target = maintenance + 250
    else:
        target = maintenance

    target = max(1400, min(3000, target))
    return int(target)


def build_prompt(profile: dict) -> str:
    json_schema_description = """
You MUST respond with ONLY valid JSON, no extra text before or after.
The JSON must have this structure:

{
  "summary": "short overview string",
  "disclaimer": "short disclaimer string",
  "days": [
    {
      "day": "Day 1",
      "workout": [
        {
          "name": "Exercise name",
          "sets": 3,
          "reps": "10-12",
          "duration_minutes": 15,
          "notes": "Short notes"
        }
      ],
      "diet": [
        {
          "meal": "Breakfast",
          "description": "What to eat",
          "approx_calories": 350
        }
      ]
    }
  ]
}
"""

    return f"""
You are helping a college student in India create a practical weekly workout and diet plan.

Student profile:
- Name (optional): {profile.get("name") or "Not provided"}
- Age: {profile["age"]}
- Gender: {profile["gender"]}
- Height: {profile["height_cm"]} cm
- Weight: {profile["weight_kg"]} kg
- BMI: {profile["bmi"]:.1f}
- Goal: {profile["goal"]}
- Activity level: {profile["activity_level"]}
- Preferred cuisine: {profile["cuisine"]}
- Daily food budget: {profile["budget"]}
- Available equipment: {profile["equipment"]}
- Time available per day for workout: {profile["time_per_day"]} minutes
- Days per week available for workout: {profile["days_per_week"]}
- Allergies or foods to avoid: {profile["allergies"] or "None specified"}
- Extra notes: {profile["notes"] or "None"}

Calorie guideline:
- Target daily calories: around {profile["target_calories"]} kcal, distributed across meals.

Constraints and requirements:
- Use common, affordable Indian student foods: roti, rice, dal, sabzi, curd, paneer, eggs, simple chicken, fruits, oats.
- Respect veg / non-veg preference and allergies strictly.
- Make the plan realistic for a hostel or student lifestyle (limited cooking, mess food).
- For workouts, design routines that match the equipment and time constraints.
- Focus on full-body training across the week, progressive but safe.
- Avoid recommending risky exercises if equipment is limited.

Output format and schema:
{json_schema_description}

Rules:
- Respond with ONLY valid JSON matching the schema.
- Do not include markdown, explanations, or any text outside the JSON.
"""


def extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


st.title("💪 AI-Powered Personalized Workout & Diet Planner")
st.caption(
    "Generates a weekly workout and diet plan tailored to college students' lifestyle, "
    "budget, and food preferences. For educational use only, not medical advice."
)

profile_tab, plan_tab, about_tab = st.tabs(
    ["👤 Profile & Inputs", "📅 Generated Plan", "ℹ️ About"]
)

with profile_tab:
    st.subheader("Enter your details")

    with st.form("profile_form"):
        col_left, col_right = st.columns(2)

        with col_left:
            name = st.text_input("Name (optional)")
            age = st.number_input("Age", min_value=16, max_value=80, value=21)
            gender = st.selectbox("Gender", ["Male", "Female"])
            height_cm = st.number_input("Height (cm)", min_value=120, max_value=220, value=170)
            weight_kg = st.number_input("Weight (kg)", min_value=35, max_value=200, value=65)

            goal = st.selectbox(
                "Primary goal",
                ["Weight loss", "Maintenance", "Muscle gain"],
                index=0,
            )
            activity_level = st.selectbox(
                "Activity level",
                ["Sedentary", "Lightly active", "Moderately active", "Very active"],
                index=1,
            )

        with col_right:
            cuisine = st.selectbox(
                "Preferred cuisine",
                ["Indian veg", "Indian non-veg", "Mixed / no preference"],
            )
            budget = st.selectbox(
                "Daily food budget",
                ["Low", "Medium", "High"],
                index=0,
            )
            equipment = st.selectbox(
                "Available equipment",
                [
                    "No equipment (hostel/room)",
                    "Basic (dumbbells/band)",
                    "Full gym access",
                ],
            )
            time_per_day = st.slider("Time per day for workout (minutes)", 15, 120, 40, 5)
            days_per_week = st.slider("Days per week for workout", 2, 7, 4)

            allergies = st.text_input("Allergies / foods to avoid (comma-separated)", "")
            notes = st.text_area(
                "Additional notes (injuries, preferences, hostel mess details, etc.)",
                "",
            )

        submitted = st.form_submit_button("Generate AI Plan", use_container_width=True)

    bmi = calculate_bmi(weight_kg, height_cm)
    target_calories = estimate_calories(
        age, gender, weight_kg, height_cm, activity_level, goal
    )

    st.markdown("---")
    st.subheader("Your basic metrics (preview)")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("BMI", f"{bmi:.1f}")
    with m2:
        st.metric("Estimated daily calories", f"{target_calories} kcal")
    with m3:
        st.metric("Planned workout frequency", f"{days_per_week} days/week")

    st.info(
        "These values are rough estimates to guide the AI plan and are **not** a substitute "
        "for professional medical or nutritional advice."
    )

    if submitted:
        st.session_state["profile"] = {
            "name": name.strip(),
            "age": age,
            "gender": gender,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "goal": goal,
            "activity_level": activity_level,
            "cuisine": cuisine,
            "budget": budget,
            "equipment": equipment,
            "time_per_day": time_per_day,
            "days_per_week": days_per_week,
            "allergies": allergies.strip(),
            "notes": notes.strip(),
            "bmi": bmi,
            "target_calories": target_calories,
        }

        with st.spinner("Generating your weekly plan..."):
            try:
                prompt = build_prompt(st.session_state["profile"])
                plan_text = generate_plan(prompt)
                st.session_state["plan_raw"] = plan_text
                st.success("Plan generated. Go to the 'Generated Plan' tab.")
            except Exception as exc:
                st.error(f"Error while generating plan: {exc}")

with plan_tab:
    st.subheader("Your AI-generated weekly workout & diet plan")

    if "plan_raw" not in st.session_state:
        st.warning("No plan generated yet. Please fill your details in the Profile tab.")
    else:
        raw = st.session_state["plan_raw"]
        clean_raw = extract_json(raw)

        try:
            plan_obj = json.loads(clean_raw)
        except json.JSONDecodeError:
            st.error("The AI response was not valid JSON. Showing raw output below.")
            st.code(raw, language="json")
        else:
            summary = (plan_obj.get("summary") or "").strip()
            disclaimer = (plan_obj.get("disclaimer") or "").strip()

            if summary:
                st.markdown(f"**Summary:** {summary}")
            if disclaimer:
                st.markdown(f"**Disclaimer:** {disclaimer}")

            days = plan_obj.get("days", [])
            if not days:
                st.warning("No day-wise data found in the plan JSON.")
            else:
                for day in days:
                    day_name = day.get("day", "Day")
                    with st.expander(day_name, expanded=False):
                        st.markdown("#### 🏋️ Workout")
                        workout_items = day.get("workout", [])
                        if workout_items:
                            for w in workout_items:
                                name = w.get("name", "Exercise")
                                sets = w.get("sets")
                                reps = w.get("reps")
                                dur = w.get("duration_minutes")
                                notes = w.get("notes", "")

                                line = f"- **{name}** — "
                                if sets is not None and reps:
                                    line += f"{sets} sets × {reps} reps"
                                if dur:
                                    line += f", ~{dur} min"
                                if notes:
                                    line += f" ({notes})"
                                st.markdown(line)
                        else:
                            st.write("No workout specified for this day.")

                        st.markdown("#### 🍽️ Diet")
                        diet_items = day.get("diet", [])
                        if diet_items:
                            total_calories = 0
                            for meal in diet_items:
                                meal_name = meal.get("meal", "Meal")
                                desc = meal.get("description", "")
                                kcal = meal.get("approx_calories")

                                if isinstance(kcal, (int, float)):
                                    total_calories += kcal

                                line = f"- **{meal_name}**: {desc}"
                                if isinstance(kcal, (int, float)):
                                    line += f" (~{int(kcal)} kcal)"
                                st.markdown(line)

                            if total_calories:
                                st.markdown(f"**Approx. daily calories:** {int(total_calories)} kcal")
                        else:
                            st.write("No diet specified for this day.")


with about_tab:
    st.subheader("About this project")
    st.markdown(
        """
**Personalized Workout & Diet Planner with AI**

- Built using Streamlit and Groq (Llama 3).  
- Collects basic student data, estimates calories, and generates a 7‑day plan as JSON.  

The app is for healthy students and educational purposes only and does not replace professional medical advice.
"""
    )
