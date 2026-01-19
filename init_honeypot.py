from app import create_app
from database import db
from model.honeypot_model import Honeypot

app = create_app()

def init_honeypot():
    with app.app_context():
        # Check if SSH honeypot exists
        ssh_hp = Honeypot.query.filter_by(name='SSH HoneyPot').first()
        if not ssh_hp:
            ssh_hp = Honeypot(
                name='SSH HoneyPot',
                type='SSH',
                port=2222,
                ip_address='0.0.0.0',
                description='Pre-configured SSH Honeypot',
                config='{"banner": "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"}',
                status='stopped'
            )
            db.session.add(ssh_hp)
            db.session.commit()
            print("SSH HoneyPot created successfully.")
        else:
            print("SSH HoneyPot already exists.")

if __name__ == '__main__':
    init_honeypot()
