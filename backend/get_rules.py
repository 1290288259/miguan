from app import app
from database import db
from model.match_rule_model import MatchRule
with app.app_context():
    rules = MatchRule.query.all()
    for r in rules:
        print(f"ID:{r.id}, Prio:{r.priority}, Type:{r.attack_type}, Name:{r.name}, Regex:{r.regex_pattern}")
