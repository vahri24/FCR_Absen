import pandas as pd
import mysql.connector  
import cv2
import urllib.request
import numpy as np
import os
from datetime import datetime
import face_recognition
import json

mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="admin",
  password="permai01",
  database="absen"
)
now = datetime.now()
tgl = now.strftime("%Y-%m-%d")
waktu = now.strftime("%H:%M:%S")
day=now.strftime("%A")

if(day == "Friday"):
    hari = "Jumat"

if(day == "Thursday"):
    hari = "Kamis"

if(day == "Wednesday"):
    hari = "Rabu"

if(day == "Tuesday"):
    hari = "Selasa"

if(day == "Monday"):
    hari = "Senin"


mycursor = mydb.cursor()

path = r'/home/fahrizal/python/dafa/FCR_Absen/image_folder'
##'''cam.bmp / cam-lo.jpg /cam-hi.jpg / cam.mjpeg '''
 
if 'Attendance.csv' in os.listdir(os.path.join(os.getcwd(),'attendace')):
    print("there iss..")
    os.remove("Attendance.csv")
else:
    df=pd.DataFrame(list())
    df.to_csv("Attendance.csv")
    
 
images = []
classNames = []
myList = os.listdir(path)
print(myList)
for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])
print(classNames)
 
 
def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList
 
 
#def markAttendance(name):
#    with open("Attendance.csv", 'r+') as f:
#        myDataList = f.readlines()
#        nameList = []
#        for line in myDataList:
#            entry = line.split(',')
#            nameList.append(entry[0])
#            if name not in nameList:
#                now = datetime.now()
#                dtString = now.strftime('%H:%M:%S')
#                f.writelines(f'\n,{name},{"hadir"},{dtString}')
 
 
encodeListKnown = findEncodings(images)
print('Encoding Complete')
 
cap = cv2.VideoCapture(0)
 
while True:
    #success, img = cap.read()
    ret, img = cap.read()
    img = cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
   
    # img = captureScreen()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
 
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
 
    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        # print(faceDis)
        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            nim = classNames[matchIndex].upper()
            sql =  "SELECT nim, nama, kelas FROM mahasiswa WHERE nim = %s"
            mycursor.execute(sql, (nim,))
            myresult = mycursor.fetchall()
            for row in myresult:
                kelas = row[2]
                nama = row[1]
            print("Pengecekan data mahasiswa pada database.")
            if(kelas):
                print("Pengecekan jadwal untuk kelas : "+kelas+", Hari : "+hari+", Jam : "+waktu)
                sql = "SELECT matkul1, matkul2, matkul3 FROM jadwal WHERE kelas=%s AND hari=%s"
                mycursor.execute(sql, (kelas, hari))
                myresult = mycursor.fetchall()
                matkul1 = []
                matkul2 = []
                matkul3 = []
                for row in myresult:
                    matkul1 = row[0]
                    matkul2 = row[1]
                    matkul3 = row[2]
                if(row):
                    kuliah1 = json.loads(matkul1)
                    kuliah2 = json.loads(matkul2)
                    kuliah3 = json.loads(matkul3)
                    print("Waktu saat ini : "+waktu)
                    if(waktu >= kuliah1["jam_mulai"] and waktu <= kuliah1["jam_akhir"]):
                        print("Cocok matkul 1")
                        sql = "SELECT * FROM absen WHERE nama=%s AND tgl = %s"
                        mycursor.execute(sql, (nama, tgl))
                        myresult = mycursor.fetchall()
                        for row in myresult:
                            sesi = row[5]
                        if not myresult:
                            print("Data belum Tersedia")
                            sql = "INSERT INTO absen (nama, nim, kelas, hari, tgl, sesi1, sesi2, sesi3) VALUES (%s,%s,%s,%s,NOW(),%s,NULL,NULL)"
                            mycursor.execute(sql, (nama, nim, kelas, hari, waktu))
                            mydb.commit()
                        else:
                            print("Data Tersedia")
                            if sesi is None:
                                print("Absen dilakukan")
                                sql = "UPDATE absen set sesi1=%s WHERE nim=%s AND nama=%s AND tgl=%s"
                                mycursor.execute(sql, (waktu, nim, nama, tgl))
                                mydb.commit()
                            else:
                                print("Sudah absen untuk sesi 1 saat ini")

                    if(waktu >= kuliah2["jam_mulai"] and waktu <= kuliah2["jam_akhir"]):
                        print("Cocok matkul 2")
                        sql = "SELECT * FROM absen WHERE nama=%s AND tgl = %s"
                        mycursor.execute(sql, (nama, tgl))
                        myresult = mycursor.fetchall()
                        for row in myresult:
                            sesi = row[6]
                        if not myresult:
                            print("Data belum Tersedia")
                            sql = "INSERT INTO absen (nama, nim, kelas, hari, tgl, sesi1, sesi2, sesi3) VALUES (%s,%s,%s,%s,NOW(),NULL,%s,NULL)"
                            mycursor.execute(sql, (nama, nim, kelas, hari, waktu))
                            mydb.commit()
                        else:
                            print("Data Tersedia")
                            if sesi is None:
                                print("Absen dilakukan")
                                sql = "UPDATE absen set sesi2=%s WHERE nim=%s AND nama=%s AND tgl=%s"
                                mycursor.execute(sql, (waktu, nim, nama, tgl))
                                mydb.commit()
                            else:
                                print("Sudah absen untuk sesi 2 saat ini")

                    if(waktu >= kuliah3["jam_mulai"] and waktu <= kuliah3["jam_akhir"]):
                        print("Cocok matkul 3")
                        sql = "SELECT * FROM absen WHERE nama=%s AND tgl = %s"
                        mycursor.execute(sql, (nama, tgl))
                        myresult = mycursor.fetchall()
                        for row in myresult:
                            sesi = row[7]
                        if not myresult:
                            print("Data belum Tersedia")
                            sql = "INSERT INTO absen (nama, nim, kelas, hari, tgl, sesi1, sesi2, sesi3) VALUES (%s,%s,%s,%s,NOW(),NULL,NULL,%s)"
                            mycursor.execute(sql, (nama, nim, kelas, hari, waktu))
                            mydb.commit()
                        else:
                            print("Data Tersedia")
                            if sesi is None:
                                print("Absen dilakukan")
                                sql = "UPDATE absen set sesi3=NOW() WHERE nim=%s AND nama=%s AND tgl=%s"
                                mycursor.execute(sql, (nim, nama, tgl))
                                mydb.commit()
                            else:
                                print("Sudah absen untuk sesi 3 saat ini")
                

            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, nama, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            #markAttendance(nama)
 
    cv2.imshow('Webcam', img)
    key=cv2.waitKey(5)
    if key==ord('q'):
        break
cv2.destroyAllWindows()
cv2.imread
