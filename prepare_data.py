import json
from data import goals, teachers

dumped_teachers = json.dumps(teachers)
dumped_goals = json.dumps(goals)

with open('teachers.json', 'w') as f:
    f.write(dumped_teachers)

with open('goals.json', 'w') as f:
    f.write(dumped_goals)