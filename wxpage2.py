#!/usr/bin/env python
# -*- coding: utf-8 -*-


from Tkinter import *
import Tkinter
import glob
import time
import matplotlib
matplotlib.use('Agg')
from PIL import Image,ImageTk
import sys
sys.path.insert(1, '/home/pi/Desktop/mat_modules')
from wifiandpic import create_pic,p_create_pic
sys.path.insert(1, '/home/pi/Desktop')
import multiprocessing

try:
    p=multiprocessing.Process(target=p_create_pic,args=())
    p.start()
    time.sleep(19) #the line "ax1.set_xticklabels([])" in create pic function sometimes is not working, the rest codes is to skip the that csv file
    if p.is_alive():
        print "pic plot problem"
        p.terminate()
        p.join()
        files=[]
        files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/*.csv')))
        upfiles = [line.rstrip('\n') for line in open('uploaded_files/mypicfile.dat','r')]
        dif_data=list(set(files)-set(upfiles))
        a=open('uploaded_files/mypicfile.dat','a+')
        [a.writelines(i+'\n') for i in dif_data]
        a.close()
        
except:
    print 'someting wrong, no new pic'
image_list = sorted(glob.glob('Desktop/Pictures/*/*.png'))
#print image_list
text_list = image_list
current = len(text_list)-1

def move(delta):
    global current, image_list
    if not (0 <= current + delta < len(image_list)):
        tkMessageBox.showinfo('End', 'No more image.')
        return
    current += delta
    image = Image.open(image_list[current])
    image = image.resize((750,360),Image.ANTIALIAS)
    #self.pw.pic = ImageTk.PhotoImage(image)
    photo = ImageTk.PhotoImage(image)
    #label['text'] = text_list[current][-24:-4]
    label['text']=''
    label['image'] = photo
    label.photo = photo

if __name__ == '__main__':
    time.sleep(5)
    root = Tk()

    label = Tkinter.Label(root, compound=Tkinter.TOP)
    label.pack()

    frame = Tkinter.Frame(root)
    frame.pack()

    Tkinter.Button(frame, text='Previous picture', command=lambda: move(-1)).pack(side=Tkinter.LEFT)
    Tkinter.Button(frame, text='Next picture', command=lambda: move(+1)).pack(side=Tkinter.LEFT)
    Tkinter.Button(frame, text='Quit', command=root.quit).pack(side=Tkinter.LEFT)

    move(0)
    #root.after(30000, lambda: root.destroy()) # Destroy the widget after 30 seconds,1000=1s
    root.mainloop()
