import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment():
    """Load environment variables from the appropriate .env file."""
    app_root = Path(__file__).resolve().parents[2]
    environments = {
        'DEV': '.dev.env',
        'PROD': '.prod.env',
    }

    # Load the base .env file first
    load_dotenv(Path(app_root) / '.env')

    # Get the environment setting
    env = os.getenv('ENV')

    # Determine the appropriate .env file to load
    env_file = environments.get(env)

    if env_file:
        dotenv_path = Path(app_root) / env_file
        load_dotenv(dotenv_path)

    # Return the required environment variables
    return (os.getenv('API_KEY'), os.getenv('API_SECRET'),
            os.getenv('LEV_API_KEY'), os.getenv('LEV_API_SECRET'),
            int(os.getenv('MAIN_LEV')), int(os.getenv('SUB_LEV')))
