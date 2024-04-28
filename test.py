from sklearn.neighbors import KNeighborsClassifier
import cv2
import pandas as pd
import pickle
import numpy as np
import os
import csv
import time
from datetime import datetime

from win32com.client import Dispatch

def speak(strl):
    speak=Dispatch(("SAPI.SpVoice"))
    speak.speak(strl)

def check_and_create_csv(filepath):
    if not os.path.isfile(filepath):
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=COL_NAMES)
            writer.writeheader()

def log_attendance(name, timestamp, is_entry, frame, x, y):
    filepath = f"Attendance/Attendance_{datetime.now().strftime('%Y-%m-%d')}.csv"
    check_and_create_csv(filepath)
    df = pd.read_csv(filepath)
    if is_entry:
        if not df[(df['NAME'] == name) & (~df['ENTRY_TIME'].isna())].empty:
            cv2.putText(frame, "Ya has pasado asistencia", (x, y-60), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            speak("Tu ya has pasado asistencia hoy")
            return
        with open(filepath, 'a+', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=COL_NAMES)
            writer.writerow({'NAME': name, 'ENTRY_TIME': timestamp, 'EXIT_TIME': '', 'ATTITUDE_SCORE': ''})
            speak("Asistencia Registrada")
    else:
        update_record_with_exit(name, timestamp, filepath, frame, x, y)

def update_record_with_exit(name, exit_time, filepath, frame, x, y):
    df = pd.read_csv(filepath)
    condition = (df['NAME'] == name) & (df['EXIT_TIME'].isna())
    if condition.any():
        idx = df[condition].index[0]
        df.at[idx, 'EXIT_TIME'] = exit_time
        df.at[idx, 'ATTITUDE_SCORE'] = calculate_attitude_score(df.at[idx, 'ENTRY_TIME'], exit_time)
        df.to_csv(filepath, index=False)
        speak("Salida Registrada")
    else:
        cv2.putText(frame, "No entry found to log exit", (x, y-60), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
        speak("Aun no pasas asistencia")


def calculate_attitude_score(entry_time, exit_time):
    fmt = "%H:%M-%S"
    entry_dt = datetime.strptime(entry_time, fmt)
    exit_dt = datetime.strptime(exit_time, fmt)
    duration = (exit_dt - entry_dt).total_seconds() / 3600 
    return max(0, 10 - (8 - duration) * 2)  


video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')


with open('data/names.pkl', 'rb') as f:
    LABELS=pickle.load(f)

with open('data/faces_data.pkl','rb') as f:
    FACES=pickle.load(f)

knn=KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)


imgBackground=cv2.imread("background.png")

COL_NAMES = ['NAME', 'ENTRY_TIME', 'EXIT_TIME', 'ATTITUDE_SCORE']

while True:

    ret, frame = video.read()
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces=facedetect.detectMultiScale(gray, 1.3, 5)

    for(x,y,w,h) in faces:
        crop_img = frame[y: y+h, x:x+w, :]
        resized_img = cv2.resize(crop_img, (50,50)).flatten().reshape(1, -1)
        ouput=knn.predict(resized_img)
        ts=time.time()
        date=datetime.fromtimestamp(ts).strftime("%d-%m-%y")
        timestamp=datetime.fromtimestamp(ts).strftime("%H:%M-%S")
        exist=os.path.isfile("Attendance/Attendance_" + date + ".csv")
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,0,255), 1)
        cv2.rectangle(frame, (x,y), (x+w, y+h), (50,50,255), 2)
        cv2.rectangle(frame, (x,y-40), (x+w, y), (50,50,255), -1)
        cv2.putText(frame, str(ouput[0]), (x,y-15), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255,255), 1)
        cv2.rectangle(frame,(x,y), (x+w, y+h), (50,50,255), 1)
        attendance=[str(ouput[0]), str(timestamp)]

    
    imgBackground[162:162 + 480, 55:55 + 640] = frame

    if ret:
        cv2.imshow("frame", imgBackground)
    

    k = cv2.waitKey(1)
    if k == ord('e'): 
        log_attendance(str(ouput[0]), timestamp, is_entry=True, frame=frame, x=x, y=y)
    elif k == ord('x'): 
        log_attendance(str(ouput[0]), timestamp, is_entry=False, frame=frame, x=x, y=y)
    elif k == ord('q'):
        break


video.release()
cv2.destroyAllWindows()