
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSUL_DB_NAME = os.path.join(BASE_DIR, 'data', 'insulation.db')
DATA_FILE = os.path.join(BASE_DIR, 'assets', 'material.json')

os.makedirs(os.path.dirname(INSUL_DB_NAME), exist_ok=True)
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)