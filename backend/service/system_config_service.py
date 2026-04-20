import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'system_config.json')

class SystemConfigService:
    @staticmethod
    def _load_config():
        if not os.path.exists(CONFIG_FILE):
            return {
                "brute_force_auto_block": False,
                "brute_force_block_duration": 24
            }
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "brute_force_auto_block": False,
                "brute_force_block_duration": 24
            }
    
    @staticmethod
    def _save_config(config):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def get_brute_force_config():
        config = SystemConfigService._load_config()
        return {
            "auto_block": config.get("brute_force_auto_block", False),
            "block_duration": config.get("brute_force_block_duration", 24)
        }

    @staticmethod
    def set_brute_force_config(auto_block: bool, block_duration: int = 24):
        config = SystemConfigService._load_config()
        config["brute_force_auto_block"] = auto_block
        if block_duration is not None:
            config["brute_force_block_duration"] = block_duration
        SystemConfigService._save_config(config)
        return True
