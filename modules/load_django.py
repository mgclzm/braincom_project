import sys
import os
from pathlib import Path
import django

PROJECT_DIR = Path(__file__).resolve().parent.parent / 'braincom_project'

sys.path.append(str(PROJECT_DIR))
os.environ['DJANGO_SETTINGS_MODULE'] = 'braincom_project.settings'
django.setup()