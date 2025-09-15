import yaml

from logger.custom_logger import CustomLogger

logger = CustomLogger().get_logger(__name__)  

def load_config(config_path: str = 'config\config.yaml') -> dict:
    """Load a YAML configuration file and return its contents as a dictionary.

    Args:
        file_path (str): The path to the YAML configuration file.

    Returns:
        dict: The contents of the YAML file as a dictionary.

        config_path defaults to 'config.yaml'.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
        print(config)
    return config

if __name__ == "__main__":
    load_config("config\config.yaml")
    logger.info("Configuration file loaded successfully", config_path="config\config.yaml")
