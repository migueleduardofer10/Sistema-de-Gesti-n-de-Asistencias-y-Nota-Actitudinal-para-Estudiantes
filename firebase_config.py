import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('sistema-gestion-asistencias-firebase-adminsdk-r6ujg-98d4db8bc5.json')
firebase_admin.initialize_app(cred)

db = firestore.client()
