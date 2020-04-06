#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 15:05:45 2020
get rockblock data from studentdrifters.org, and save them.
@author: hxu
"""

from matplotlib.dates import date2num
import time
import pysftp
import os
import sys
import subprocess
from dateutil import parser
import glob
import json
import datetime
import numpy as np
import urllib
from dateutil import parser
def read_codes():
  # get id,depth from /data5/jmanning/drift/codes.dat, need to change the path1
  inputfile1="codes_temp.dat"
  #path1="/net/data5/jmanning/drift/"
  path1='/home/hxu/Downloads/'
  f1=open(path1+inputfile1,'r')
  esn,id,depth=[],[],[]
  for line in f1:
    esn.append(line.split()[0])
    id.append(line.split()[1])
    depth.append(line.split()[2]) 
 	

  return esn, id,depth
esn2, ide,depth=read_codes()# get the id,depth from /data5/jmanning/drift/codes.dat,
esn,dates,lat,lon,battery,data_send,meandepth,rangedepth,timelen,meantemp,sdeviatemp=[],[],[],[],[],[],[],[],[],[],[], 
date_time,year,month,day,hour,minute,second,yearday=[],[],[],[],[],[],[],[] 
#esn2, ide,depth=read_codes()
rockdata=[]
link='https://studentdrifters.org/posthuanxin/rockemolt.dat'
from urllib.request import urlopen
f = urlopen(link)
myfile = f.read()
print(myfile)
lines=myfile.splitlines()# put everyling into a list
datas,esn,transmit_time=[],[],[]
for i in range(len(lines)):
    datas.append(bytearray.fromhex(str(lines[i]).split('data=')[1].split("'")[0]).decode()) # format byte data to string and add to "datas" list
    esn.append(str(lines[i]).split('imei=')[1].split('&')[0])
    transmit_time.append(str(lines[i]).split('transmit_time=')[1].split('&iridium')[0])
    lat.append(float(bytearray.fromhex(str(lines[i]).split('data=')[1].split("'")[0]).decode().split(',')[0]))
    lon.append(float(bytearray.fromhex(str(lines[i]).split('data=')[1].split("'")[0]).decode().split(',')[1]))
    meandepth.append(float(bytearray.fromhex(str(lines[i]).split('data=')[1].split("'")[0]).decode().split(',')[2][0:3]))   
    rangedepth.append(float(bytearray.fromhex(str(lines[i]).split('data=')[1].split("'")[0]).decode().split(',')[2][3:6]))
    timelen.append(float(bytearray.fromhex(str(lines[i]).split('data=')[1].split("'")[0]).decode().split(',')[2][6:9])/1000)
    meantemp.append(float(bytearray.fromhex(str(lines[i]).split('data=')[1].split("'")[0]).decode().split(',')[2][9:13])/100)
    sdeviatemp.append(float(bytearray.fromhex(str(lines[i]).split('data=')[1].split("'")[0]).decode().split(',')[2][13:17])/100)
    dates.append(transmit_time[i][0:8]+transmit_time[i][11:13]+transmit_time[i][16:18]+transmit_time[i][21:23])
    date_time.append(datetime.datetime.strptime(dates[i],"%y-%m-%d%H%M%S" ))
    year.append(str(date_time[i].year))
    month.append(str(date_time[i].month))
    day.append(str(date_time[i].day))
    hour.append(str(date_time[i].hour))
    minute.append(str(date_time[i].minute))
    second.append(str(date_time[i].second))
    yearday.append(int(date_time[i].strftime('%j'))+date_time[i].hour/24+date_time[i].minute/24./60.) # get yearday


f_output=open('ap3_'+  str(datetime.datetime.now())[:16]+'.dat','w') #open a ouput file,change paths if needed
index_idn1=[]
    
for o in range(len(dates)):
    if meantemp[o]<30:
          index_idn1=(np.where(esn[o][-6:]==np.array(ide)))[0][0] # index of the codes_temp file
          id_idn1=esn2[index_idn1] # where is the consecutive time this unit was used
          depth_idn1=-1.0*float(depth[index_idn1]) # make depth negative
          #f_output=open('ap3_'+  str(datetime.datetime.now())[:16]+'.dat', 'w')
          f_output.write(str(id_idn1).rjust(10)+" "+str(esn[o][-7:]).rjust(7)+ " "+str(month[o]).rjust(2)+ " " +
                  str(day[o]).rjust(2)+" " +str(hour[o]).rjust(3)+ " " +str(minute[o]).rjust(3)+ " " )
          f_output.write(("%10.7f") %(yearday[o]))
          #f_output.write(" "+str(lon).rjust(10)+' '+str(lat).rjust(10)+ " " +str(float(depth_idn1)).rjust(4)+ " "
          #        +str(np.nan))
          f_output.write(" "+("%10.5f") %-(lon[o]%100/60+int(lon[o]/100))+' '+("%10.5f") %(lat[o]%100/60+int(lat[o]/100))+' '+str(float(depth_idn1)).rjust(4)+ " "+'nan')
          #f_output.write(" "+str(meandepth).rjust(10)+' '+str(rangedepth).rjust(10)+' '+str(len_day).rjust(10)+  " " +str(mean_temp).rjust(4)+ " "
          #        +str(sdevia_temp)+'\n')            
          f_output.write(" "+str(meandepth[o]).rjust(10)+' '+str(rangedepth[o]).rjust(10)+' '+str(timelen[o]).rjust(10)+  " " +("%6.2f") %(meantemp[o])+ " "
                  +("%6.2f") %(sdeviatemp[o])+("%6.0f") %(int(year[o]))+'\n')  
          
f_output.close()          
