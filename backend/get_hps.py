from app import app
from database import db
from model.honeypot_model import Honeypot
with app.app_context():
    hps = Honeypot.query.all()
    for hp in hps:
        print(f"ID:{hp.id}, Name:{hp.name}, Type:{hp.type}, Port:{hp.port}, Status:{hp.status}")
