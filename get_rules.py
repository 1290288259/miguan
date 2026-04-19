import sys
sys.path.append('backend')
from backend.app import app
from backend.database import db
from backend.model.match_rule_model import MatchRule
with app.app_context():
    rules = MatchRule.query.all()
    for r in rules:
        print(f"ID:{r.id}, Name:{r.name}, Regex:{r.rule_content}, Type:{r.attack_type}")
