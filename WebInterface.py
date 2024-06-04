from flask import Flask,render_template,request,jsonify,redirect,url_for
import sys, random, threading,sqlite3,configparser,datetime
from pathlib import Path
from tkinter import *
from tkinter import messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)


conn = sqlite3.connect('Smart_House',check_same_thread=False)
c = conn.cursor()
c.execute('''
          CREATE TABLE IF NOT EXISTS settings
          ([setting_id] INTEGER PRIMARY KEY AUTOINCREMENT, [lower] REAL, [upper] REAL)
          ''')
c.execute('''
          CREATE TABLE IF NOT EXISTS temps
          ([temp_id] INTEGER PRIMARY KEY AUTOINCREMENT, [temp] REAL, [time] TEXT)
          ''')
conn.commit()
kitchen = "off"
room1 = "off"
room2 = 0
m1 = 14
m2 = 31
n1 = 22.4
n2 = 23.6
c.execute("insert or ignore into settings (setting_id, lower, upper) values (?, ?, ?)", (1,float(n1),float(n2)))
conn.commit()
timelist = []
templist = []
temperature = round(random.uniform(m1,m2),2)
timelist.append(datetime.datetime.now().strftime('%H:%M:%S'))
templist.append(temperature)
heat = False
heatstr = "Увімкнена"
synced = True

config = configparser.ConfigParser()
path = Path('config.ini')
def createConfig():
  global config,n1,n2
  config.add_section("temp")
  config.set("temp", "lower", str(n1))
  config.set("temp", "upper", str(n2))
  with open("config.ini", 'w') as file:
   config.write(file)
def loadConfig():
  global config,n1,n2
  tempparam = config["temp"]
  n1 = float(tempparam["lower"])
  n2 = float(tempparam["upper"])
def setConfig(lower, upper):
  global config,n1,n2
  config.set("temp", "lower",str(lower))
  config.set("temp", "upper", str(upper))
  with open("config.ini", 'w') as file:
   config.write(file)
if (path.is_file()):
  config.read("config.ini")
  loadConfig()
else:
  createConfig()
  config.read("config.ini")

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
def temp():
  global temperature,n1,n2,heat,heatstr,c,conn
  threading.Timer(2.6, temp).start()
  temperature = random.uniform(m1,m2) 
  if(len(timelist)>25):
    timelist.pop(0)
    templist.pop(0)
  c.execute("insert into temps (temp, time) values (?, ?)", (float(temperature),datetime.datetime.now().strftime('%H:%M:%S' )))
  conn.commit()
  timelist.append(datetime.datetime.now().strftime('%H:%M:%S'))
  templist.append(temperature)
  if(temperature<float(n1) and heat == False):
    heat = True
    heatstr = "Увімкнена"
  if(temperature>float(n2) and heat == True):
    heatstr = "Вимкнена"
    heat = False
temp()
@app.route('/',methods =['post','get'])
def index():
 global temperature,kitchen,room1,room2,n1,n2
 if request.method == 'POST':
   kitchen = request.form.get('kitchen') 
   if kitchen == None:
     kitchen = "off"
   room1 = request.form.get('room1')
   if room1 == None:
     room1 = "off"
   room2 = request.form.get('room2')
   if room2 == None:
     room2 = "0"
   print (f"Стан системи: kitchen {kitchen}, room1 {room1}, room2 {room2}",file=sys.stdout)
 return render_template('index.html', kitchen = kitchen, room1 = room1, room2 = room2, temperature = temperature,n1 = n1, n2 = n2)

@app.route('/update/',methods =['post','get'])
def update():
 global temperature,kitchen,room1,room2,n1,n2,synced,c,conn
 if request.method == 'POST':
   n1 = request.form.get('lower')
   n2 = request.form.get('upper')
   setConfig(float(n1),float(n2))
   c.execute("UPDATE settings SET lower=?,upper=?",(float(n1),float(2)))
   conn.commit()
   synced = False
   print ("Завантаження порогів з форми")
 return redirect(url_for("index"))
@app.route('/temp/',methods =['post','get'])
def getTemp():
 global temperature
 print("Перевірка температури",file=sys.stdout)
 return str(temperature)
@app.route('/graph/',methods =['post','get'])
def graph():
 global timelist,templist,n1,n2
 print("Завантаження графіку у браузері",file=sys.stdout)
 return (jsonify({"dates": timelist,"temps": templist,"n1list": [float(n1) for i in range(0,len(timelist))],"n2list":[float(n2) for i in range(0,len(timelist))]}))
@app.route('/refresh/',methods =['post','get'])
def refresh():
 global n1,n2,heatstr
 print("Синхронізація",file=sys.stdout)
 return (jsonify({"n1": n1,"n2": n2,"heating":heatstr}))

def tkApp():
  global heat,temperature,n1,n2,timelist,templist,heatstr
  window = Tk()
  window.title ("Умнов ІТШІ-20-1") 
  window.geometry ( '960x600+600+150')
  lblHeat = Label(window, text=("Обігрів: " + heatstr),font = ( "Arial Bold", 14))
  lblLower = Label(window, text="Значення нижнього порогу")
  lblUpper = Label(window, text="Значення верхнього порогу")
  lower = Entry(window)
  upper = Entry(window)
  lblUpper.pack()
  upper.pack()
  lblLower.pack()
  lower.pack()
  lblHeat.pack()
  lower.insert(0,str(n1))
  upper.insert(0,str(n2))
  fig = plt.figure(figsize=(7.5, 4))
  graphic = fig.add_subplot(1, 1, 1)
  def submit():
    global n1,n2,config,c,conn
    if(lower.get() and upper.get() and is_float(lower.get()) and is_float(upper.get())):
      if(float(lower.get()) > float(upper.get())):
        messagebox.showerror(title="Помилка", message="Значення нижнього порогу не може бути вищим за значення нижнього порогу.")
      else:
        n1 = float(lower.get())
        n2 = float(upper.get())
        setConfig(n1,n2)
        c.execute("UPDATE settings SET lower=?,upper=?",(float(n1),float(2)))
        conn.commit()
    else:
      messagebox.showerror(title="Помилка", message="Поле вводу пусте або вказано некоректне значення.")
  buttonSubmit = Button(window, text = "Внести зміни",command=submit)
  buttonSubmit.pack()
  def sync():
    global synced,n1,n2
    if(synced == False):
      lower.delete(0,END)
      lower.insert(0,str(n1))
      upper.delete(0,END)
      upper.insert(0,str(n2))
      synced = True
    window.after(1000,sync)
  def animate(i):
    global temp,heatstr
    graphic.clear()
    plt.title('Графік зміни температури')
    plt.xlabel('Час')
    plt.ylabel('Температура')
    graphic.set_ylim([10, 35])
    graphic.plot(timelist, templist,label="Поточне значення температури")
    graphic.plot(timelist,[float(n2) for i in range(0,len(timelist))],label="Верхній поріг")
    graphic.plot(timelist,[float(n1) for i in range(0,len(timelist))],label="Нижній поріг")
    graphic.legend(loc="upper left",fontsize="8")
    lblHeat.config(text=("Обігрів: " + heatstr))
    plt.xticks(rotation=45)
    plt.subplots_adjust(bottom=0.30)
    sync()
  ani = FuncAnimation(fig, animate, interval=2600, repeat=False)
 
  canvas = FigureCanvasTkAgg(fig, master=window)
  canvas.draw()
  canvas.get_tk_widget().pack()
  window.mainloop()
tkapp = threading.Thread(target = tkApp, daemon = True).start()
webApp = threading.Thread(target = app.run(),  daemon = True).start()
