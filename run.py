"""Application entry point."""

import os

from app import create_app
from app.config import config_by_name

# Get configuration from environment
config_name = os.getenv("FLASK_ENV", "development")
config_class = config_by_name.get(config_name, config_by_name["default"])

app = create_app(config_class)

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "7770"))
    app.run(host="0.0.0.0", port=port)
