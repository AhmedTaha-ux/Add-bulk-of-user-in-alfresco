import os
from dotenv import load_dotenv

load_dotenv()

ALFRESCO_USERNAME = os.getenv("ALFRESCO_USERNAME")
ALFRESCO_PASSWORD = os.getenv("ALFRESCO_PASSWORD")
ALFRESCO_URL = os.getenv("ALFRESCO_URL")
UPDATE_URL = os.getenv("UPDATE_URL")
