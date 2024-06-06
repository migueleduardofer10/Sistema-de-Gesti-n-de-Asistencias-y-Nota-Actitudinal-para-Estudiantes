import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if not cred_path:
    raise ValueError("No se ha definido la variable de entorno 'GOOGLE_APPLICATION_CREDENTIALS'")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()
