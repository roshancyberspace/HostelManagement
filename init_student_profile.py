from modules.student_profile.models import (
    init_student_profile_table,
    init_student_behaviour_table
)

if __name__ == "__main__":
    init_student_profile_table()
    init_student_behaviour_table()
    print("✅ Student Profile & Behaviour tables initialized successfully")
