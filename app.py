import MySQLdb
import cv2
import os
from flask import Flask, request,render_template,session
from datetime import date
from datetime import datetime
import numpy as np
import pickle
from werkzeug.utils import secure_filename

from time import sleep
from flask_session import Session
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import face_recognition

#### Defining Flask App
app = Flask(__name__)
app.config["SESSION_PERMANENT"]=False
app.config["SESSION_TYPE"]="filesystem"
Session(app)

####connect db
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='test'
mysql=MySQL(app)

##mailconnect
app.config['MAIL_SERVER']='smtp.googlemail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='Your email'
app.config['MAIL_PASSWORD']='app password created in google security'
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail=Mail(app)

upload_folder=os.path.join('static','temp')
app.config['UPLOAD']=upload_folder

#### Saving Date today in 2 different formats
now=datetime.now()
today=date.today()
def datetoday2():
    return today.strftime("%d-%B-%Y")
def datetoday():
    return today.strftime("%m_%d_%y")
def totalreg():
    return (len(os.listdir('static/imgsss')))
#markattendance in DB
def markAttendance(name):
    with open('Attendance.csv','r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
        if name not in nameList:
            now = datetime.now()
            time = now.strftime('%I:%M:%S:%p')
            date = now.strftime('%d-%B-%Y')
            f.writelines(f'\n{name}, {time}, {date}')
    username = name.split('_')[0]
    userid = name.split('_')[1]
    mail=name.split('_')[2]
    now = datetime.now()
    time = now.strftime('%I:%M:%S:%p')
    date = now.strftime('%d-%B-%Y')
    subject=session['subject']
    teachername=session['username']
    slot1=session['slot']
    cur=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM attendance where subject= %s AND date=%s AND roll=%s',(subject,date,userid,))
    result=cur.fetchone()
    if not result:
        cur.execute('INSERT INTO attendance (name,roll,subject,email,teacher,slot,time,date) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)', (username,userid,subject,mail,teachername,slot1,time,date,))
        mysql.connection.commit()
tt=0
path = 'static/imgsss'
images = []
classNames = []

    #extract images
def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encoded_face = face_recognition.face_encodings(img)[0]
        encodeList.append(encoded_face)
    return encodeList
def extract_attendance():
    subject=session['subject']
    teachername=session['username']
    slot1=session['slot']
    ate1=datetoday2()
    cur1=mysql.connection.cursor()
    cur1.execute('SELECT * FROM attendance WHERE teacher= %s AND slot= %s AND date=%s AND subject=%s', (teachername,slot1,ate1,subject,))
    accoun1=cur1.fetchall()
    l=len(accoun1)
    names=[]
    rolls=[]
    subjects=[]
    emails=[]
    teachers=[]
    slots=[]
    times=[]
    dates=[]
    for i in accoun1:
        names.append(i[0])
        rolls.append(i[1])
        subjects.append(i[2])
        emails.append(i[3])
        teachers.append(i[4])
        slots.append(i[5])
        times.append(i[6])
        dates.append(i[7])
        # print(names)
    return names,rolls,subjects,emails,teachers,slots,times,dates,l

mess=''
#### Our main page
@app.route('/')
def mainpage():
    if not session.get('logged_in'):
        return render_template('login.html',mess=mess)
    return render_template('home.html')

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.method=="POST":
        userNam = request.form['usernamee']
        passwor = request.form['passworde']
        slot=request.form['slot']
        session['slot']=slot
    cur=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT teacherMail,subject,slot,teacher_name FROM admin WHERE teacherMail= %s AND password= %s and slot= %s', (userNam,passwor,slot,))
    accoun=cur.fetchone()
    global teachername
    global subject
    global slot1
    if accoun:
        session['logged_in']=True
        teachername = accoun["teacher_name"]
        session['username']=accoun["teacher_name"]
        session['subject'] = accoun["subject"]
        slot1=accoun["slot"]
        #print(teachername+" "+session['username']+session['subject'])
    else:
        global mess
        mess="Login failed! enter correct credintials"
    return mainpage()

@app.route('/encoding',methods=['GET','POST'])
def encoding():
    if totalreg()==0:
        mess="Database is empty please add the members and click encoding"
        names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()   
        return render_template('home.html',names=names,rolls=rolls,subjects=subjects,l=l,emails=emails,teachers=teachers,slots=slots,times=times,mess=mess,dates=dates,totalreg=totalreg())
    
#import images
    mylist = os.listdir(path)
    if os.path.exists("EncodeFile.p"):
        os.remove("EncodeFile.p")
    file=open("EncodeFile.p",'wb')
    for cl in mylist:
        curImg = cv2.imread(f'{path}/{cl}')
        images.append(curImg)
    #names
        classNames.append(os.path.splitext(cl)[0])
        fileName=f'{path}/{cl}'
    #encoding images
    print("encoding")
    encoded_face_train = findEncodings(images)
    encode_ids=[encoded_face_train,images]
    #file=open("EncodeFile.pkl", 'wb')
    pickle.dump(encode_ids,file)
    file.close()
    print("file saved")
    mess="encoded successfully"
    global tt
    tt=0
    names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()   
    return render_template('home.html',names=names,rolls=rolls,subjects=subjects,l=l,emails=emails,teachers=teachers,slots=slots,times=times,mess=mess,dates=dates,totalreg=totalreg())

#logout
@app.route('/logout')
def logout():
    session['logged_in']=False
    global mess
    mess="logout successfully!"
    return mainpage()
##############################################################################################################
@app.route('/home',methods=['GET','POST'])
def home():
    if not session.get('logged_in'):
        mess="nice try first login"
        return render_template('login.html',mess=mess)
    names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance() 
    #print(results)   
    return render_template('home.html',names=names,rolls=rolls,subjects=subjects,emails=emails,teachers=teachers,slots=slots,times=times,l=l,dates=dates,totalreg=totalreg()) 
#### This function will run when we click on Take Attendance Button
@app.route('/start',methods=['GET'])
def start():
    if not session.get('logged_in'):
        mess="no redirecting first login"
        return render_template('login.html',mess=mess)
    if tt==1 :
        mess="After adding student please click encoding"
        names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()   
        return render_template('home.html',names=names,rolls=rolls,subjects=subjects,l=l,emails=emails,teachers=teachers,slots=slots,times=times,mess=mess,dates=dates,totalreg=totalreg())
    to=totalreg()
    if to==0:
        mess="Database is empty please add the members"
        names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()   
        return render_template('home.html',names=names,rolls=rolls,subjects=subjects,l=l,emails=emails,teachers=teachers,slots=slots,times=times,mess=mess,dates=dates,totalreg=totalreg())
    
    cap  = cv2.VideoCapture(0)
    key=cv2.waitKey(1) 
    file=open('EncodeFile.p','rb')
    encodeListWithids= pickle.load(file)
    file.close()
    path = 'static/imgsss'
    images = []
    classNames = []
    mylist = os.listdir(path)
    for cl in mylist:
            curImg = cv2.imread(f'{path}/{cl}')
            images.append(curImg)
            classNames.append(os.path.splitext(cl)[0])
    encodeListKnown, studentIds=encodeListWithids
    print("encode file loaded")
    while True:
        success, img = cap.read()
        imgS = cv2.resize(img, (0,0), None, 0.25,0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
        faces_in_frame = face_recognition.face_locations(imgS)
        encoded_faces = face_recognition.face_encodings(imgS, faces_in_frame)
        for encode_face, faceloc in zip(encoded_faces,faces_in_frame):
            matches = face_recognition.compare_faces(encodeListKnown, encode_face)
            faceDist = face_recognition.face_distance(encodeListKnown, encode_face)
            matchIndex = np.argmin(faceDist)
            print("matches", matches)
            print("faceDis",faceDist)
            print(matchIndex)
            name='unknown'
            if matches[matchIndex]:
                #print(classNames)
                name1 = classNames[matchIndex]
                name = name1.split('_')[0]
                y1,x2,y2,x1 = faceloc
                y1, x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
                cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
                cv2.rectangle(img, (x1,y2-35),(x2,y2), (0,255,0), cv2.FILLED)
                cv2.putText(img,name, (x1+6,y2-5), cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2)
                markAttendance(name1)
            else:
                y1,x2,y2,x1 = faceloc
                y1, x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
                cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,255),2)
                cv2.rectangle(img, (x1,y2-35),(x2,y2), (0,255,255), cv2.FILLED)
                cv2.putText(img,name, (x1+6,y2-5), cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2)
        cv2.imshow('webcam', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()   
    return render_template('home.html',names=names,rolls=rolls,subjects=subjects,l=l,emails=emails,teachers=teachers,slots=slots,times=times,dates=dates,totalreg=totalreg())

@app.route('/start1',methods=['GET'])
def start1():
    if not session.get('logged_in'):
        mess="no redirecting first login"
        return render_template('login.html',mess=mess)
    if tt==1:
        mess="After adding student please click encoding"
        names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()   
        return render_template('home.html',names=names,rolls=rolls,subjects=subjects,l=l,emails=emails,teachers=teachers,slots=slots,times=times,mess=mess,dates=dates,totalreg=totalreg())
    to=totalreg()
    if to==0:
        mess="Database is empty please add the members"
        names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()   
        return render_template('home.html',names=names,rolls=rolls,subjects=subjects,l=l,emails=emails,teachers=teachers,slots=slots,times=times,mess=mess,dates=dates,totalreg=totalreg())
    
    cap  = cv2.VideoCapture(0)
    key=cv2.waitKey(1) 
    file=open('EncodeFile.p','rb')
    encodeListWithids= pickle.load(file)
    file.close()
    path = 'static/imgsss'
    images = []
    classNames = []
    mylist = os.listdir(path)
    for cl in mylist:
            curImg = cv2.imread(f'{path}/{cl}')
            images.append(curImg)
            classNames.append(os.path.splitext(cl)[0])
    encodeListKnown, studentIds=encodeListWithids
    print("encode file loaded")
    while True:
        success, img = cap.read()
        ee=img
        cv2.imshow('attendance',ee)
        if cv2.waitKey(1) & 0xFF == ord('e'):
            imgS = cv2.resize(img, (0,0), None, 0.25,0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
            faces_in_frame = face_recognition.face_locations(imgS)
            encoded_faces = face_recognition.face_encodings(imgS, faces_in_frame)
            for encode_face, faceloc in zip(encoded_faces,faces_in_frame):
                matches = face_recognition.compare_faces(encodeListKnown, encode_face)
                faceDist = face_recognition.face_distance(encodeListKnown, encode_face)
                matchIndex = np.argmin(faceDist)
                print("matches", matches)
                print("faceDis",faceDist)
                print(matchIndex)
                name='unknown'
            #if found display
                if matches[matchIndex]:
                    print(classNames)
                    name1 = classNames[matchIndex]
                    name = name1.split('_')[0]
                    y1,x2,y2,x1 = faceloc
                    y1, x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
                    cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
                    cv2.rectangle(img, (x1,y2-35),(x2,y2), (0,255,0), cv2.FILLED)
                    cv2.putText(img,name, (x1+6,y2-5), cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2)
                    markAttendance(name1)
                else:
                    y1,x2,y2,x1 = faceloc
                    y1, x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
                    cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,255),2)
                    cv2.rectangle(img, (x1,y2-35),(x2,y2), (0,255,255), cv2.FILLED)
                    cv2.putText(img,name, (x1+6,y2-5), cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2)
                cv2.imshow('webcam', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            break
    
    names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance() 
        #print(results)   
    return render_template('home.html',names=names,rolls=rolls,subjects=subjects,l=l,emails=emails,teachers=teachers,slots=slots,times=times,dates=dates,totalreg=totalreg())

@app.route('/add',methods=['GET','POST'])
def add():
    if not session.get('logged_in'):
        mess="no redirecting first login"
        return render_template('login.html',mess=mess)
    newusername = request.form['newusername']
    newuserid = request.form['newuserid']
    mail=request.form['mail']
    key=cv2.waitKey(1)
    cap = cv2.VideoCapture(0)
    while True:
        _,frame = cap.read()
        cv2.imshow("capture",frame)
        key=cv2.waitKey(1)
        if key==ord('s'):
            name = newusername+'_'+str(newuserid)+'_'+mail+'_'+'.jpeg'
            path='static/imgsss/'
            imgf=cv2.imwrite(f'{path}{name}',frame)
            global tt
            tt=1
            break
        elif key==ord('q'):
            cap.release()
            break
    cv2.destroyAllWindows()
    names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()
    #print(results)
    return render_template('home.html',names=names,rolls=rolls,subjects=subjects,emails=emails,teachers=teachers,slots=slots,times=times,dates=dates,l=l,totalreg=totalreg())

@app.route('/addimg',methods=['GET','POST'])
def addimg():
    if not session.get('logged_in'):
        mess="no redirecting first login"
        return render_template('login.html',mess=mess)
    newusername = request.form['newusername']
    newuserid = request.form['newuserid']
    mail=request.form['mail']
    f=request.files['img']
    filename=secure_filename(f.filename)
    f.save(os.path.join(app.config['UPLOAD'], filename))
    path='static/temp/'
    global tt
    mylist = os.listdir(path)
    for cl in mylist:
        curImg = cv2.imread(f'{path}/{cl}')
        path1='static/imgsss/'
        name = newusername+'_'+str(newuserid)+'_'+mail+'_'+'.jpeg'
        imgf=cv2.imwrite(f'{path1}{name}',curImg)
        os.remove(os.path.join(path,cl))
        tt=1
    names,rolls,subjects,emails,teachers,slots,times,dates,l = extract_attendance()
    #print(results)
    return render_template('home.html',names=names,rolls=rolls,subjects=subjects,emails=emails,teachers=teachers,slots=slots,times=times,dates=dates,l=l,totalreg=totalreg())

######################################################################################################
#new page

x=2
student=None
datee=None
mgg=''
@app.route('/page',methods=['GET','POST'])
def page():
    if not session.get('logged_in'):
        mess="no redirecting first login"
        return render_template('login.html',mess=mess)
    if x==1:
        names,rolls,subjects,emails,teachers,slots,times,dates,l=stu_base()
        return render_template('page.html',names=names,rolls=rolls,subjects=subjects,emails=emails,teachers=teachers,slots=slots,times=times,dates=dates,l=l,messa=mgg)
    elif x==0:
        names,rolls,subjects,emails,teachers,slots,times,dates,l=stu_base_date()
        return render_template('page.html',names=names,rolls=rolls,subjects=subjects,emails=emails,teachers=teachers,slots=slots,times=times,dates=dates,l=l,messa=mgg)
    else:
        return render_template('page.html',messa=mgg)
    
def stu_base():
    subject=session['subject']
    teachername=session['username']
    slot1=session['slot']
    stude=student
    cur1=mysql.connection.cursor()
    cur1.execute('SELECT * FROM attendance WHERE teacher= %s AND slot= %s AND name=%s AND subject=%s', (teachername,slot1,stude,subject,))
    accoun1=cur1.fetchall()
    #print(len(accoun1))
    print(accoun1)
    l=len(accoun1)
    names=[]
    rolls=[]
    subjects=[]
    emails=[]
    teachers=[]
    slots=[]
    times=[]
    dates=[]
    for i in accoun1:
        names.append(i[0])
        rolls.append(i[1])
        subjects.append(i[2])
        emails.append(i[3])
        teachers.append(i[4])
        slots.append(i[5])
        times.append(i[6])
        dates.append(i[7])
        #print(names)
    return names,rolls,subjects,emails,teachers,slots,times,dates,l

def stu_base_date():
    subject=session['subject']
    teachername=session['username']
    slot1=session['slot']
    stude=datee
    cur1=mysql.connection.cursor()
    cur1.execute('SELECT * FROM attendance WHERE teacher= %s AND slot= %s AND date=%s AND subject=%s', (teachername,slot1,stude,subject,))
    accoun1=cur1.fetchall()
    #print(len(accoun1))
    #print(accoun1)
    l=len(accoun1)
    names=[]
    rolls=[]
    subjects=[]
    emails=[]
    teachers=[]
    slots=[]
    times=[]
    dates=[]
    for i in accoun1:
        names.append(i[0])
        rolls.append(i[1])
        subjects.append(i[2])
        emails.append(i[3])
        teachers.append(i[4])
        slots.append(i[5])
        times.append(i[6])
        dates.append(i[7])
        print(names)
    return names,rolls,subjects,emails,teachers,slots,times,dates,l

@app.route('/student',methods=['GET','POST'])
def student():
    if not session.get('logged_in'):
        mess="no redirecting first login"
        return render_template('login.html',mess=mess)
    if request.method=="POST":
        global student
        global x
        student=request.form['name']
        x=1
    return page()

@app.route('/date',methods=['GET','POST'])
def date():
    if not session.get('logged_in'):
        mess="no redirecting first login"
        return render_template('login.html',mess=mess)
    if request.method=="POST":
        global datee
        global x
        datee=request.form['date']
        x=0
    return page()

@app.route('/sendmail',methods=['GET','POST'])
def sendmail():
    if not session.get('logged_in'):
        mess="no redirecting first login"
        return render_template('login.html',mess=mess)
    subject=session['subject']
    teachername=session['username']
    slot1=session['slot']
    ate1=datetoday2()
    cur1=mysql.connection.cursor()
    cur1.execute('SELECT email,name,subject FROM attendance WHERE teacher= %s AND slot= %s AND date=%s AND subject=%s', (teachername,slot1,ate1,subject,))
    accoun1=cur1.fetchall()
    #print(accoun1)
    ll=[]
    subb=""
    for i in accoun1:
        ll.append(i[0])
        if len(subb)==0:
            subb=i[2]
    a="Attendance of "+subb
    aa="Hello,  Your attendance for "+i[2]+" has updated successfully"
    msg=Message(a,sender='noreply@demo.com',recipients=ll)
    msg.body=aa
    mail.send(msg)
    global mgg
    mgg="email sent successfully"
    return page()

#### Our main function which runs the Flask App
if __name__ == '__main__':
    app.run(debug=True)