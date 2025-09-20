from pathlib import Path
import os
import yaml
from logger import GLOBAL_LOGGER as log

#from logger.custom_logger import CustomLogger
#logger = CustomLogger().get_logger(__name__)  

def _project_root() -> Path:
    # .../utils/config_loader.py -> parents[1] == project root
    return Path(__file__).resolve().parents[1]

def load_config(config_path: str | None = None) -> dict:
    """Load a YAML configuration file and return its contents as a dictionary.

    Args:
        file_path (str): The path to the YAML configuration file.

    Returns:
        dict: The contents of the YAML file as a dictionary.

        config_path defaults to 'config.yaml'.
    """

    env_path = os.getenv("CONFIG_PATH")
    if config_path is None:
        config_path = env_path or str(_project_root() / "config" / "config.yaml")

    path = Path(config_path)
    if not path.is_absolute():
        path = _project_root() / path

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, 'r', encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return config

# if __name__ == "__main__":
#     load_config("config\config.yaml")
#     log.info("Configuration file loaded successfully", config_path="config\config.yaml")
