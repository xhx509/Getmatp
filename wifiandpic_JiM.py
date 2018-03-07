# routine to process Aquatech 530TD data
# modeled after Yacheng's "emolt_pd.py"
# where it plots the record and generates output file
#
import glob
import ftplib
import shutil
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import datetime
from pylab import *
import pandas as pd
from pandas import *
import time
import os
import numpy as np
from gps import *
from time import *
import threading
#from datetime import datetime
def parse(datet):
    from datetime import datetime
    dt=datetime.strptime(datet,'%Y-%m-%dT%H:%M:%S')
    #print type(dt)
    #dt=datetime.strptime(datet,'%m/%d/%Y %I:%M:%S %p')
    #dt=datetime.strptime(datet,'%H:%M:%S %m/%d/%Y')
    return dt

def parse2(datet):
    from datetime import datetime
    dt=datetime.strptime(datet,'%Y-%m-%d %H:%M:%S')
    #dt=datetime.strptime(datet,'%m/%d/%Y %I:%M:%S %p')
    #dt=datetime.strptime(datet,'%H:%M:%S %m/%d/%Y')
    return dt    
def gmt_to_eastern(times_gmt):
    import datetime
    times=[]
    eastern = pytz.timezone('US/Eastern')
    gmt = pytz.timezone('GMT')
    #date = datetime.datetime.strptime(filename, '%a, %d %b %Y %H:%M:%S GMT')
    for i in range(len(times_gmt)):
        date = datetime.datetime.strptime(str(times_gmt[i]),'%Y-%m-%d %H:%M:%S')
        date_gmt=gmt.localize(date)
        easterndate=date_gmt.astimezone(eastern)
        times.append(easterndate)

    return times

'''
Modify input file below only if you need 
'''

def p_create_pic():

      tit='Temperature and Depth' # plot title
      
      if not os.path.exists('/home/pi/Desktop/Pictures'):
        os.makedirs('/home/pi/Desktop/Pictures') 

      if not os.path.exists('uploaded_files'):
        os.makedirs('uploaded_files')
      n=0  
      
      try:
            files=[]
            files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/*.csv')))
            
            if not os.path.exists('uploaded_files/mypicfile.dat'):
                open('uploaded_files/mypicfile.dat','w').close() 
            
            with open('uploaded_files/mypicfile.dat','r') as f:
                content = f.readlines()
                f.close()
            
            upfiles = [line.rstrip('\n') for line in open('uploaded_files/mypicfile.dat','r')]
            dif_data=list(set(files)-set(upfiles)) # returns all the new files that have not been uploaded
           
            if dif_data==[]:
                print 'No new plots were found so we will look at old ones'
                print 'Stand by ..'
                time.sleep(3)
                pass
    ##################################
            dif_data.sort(key=os.path.getmtime)# sort new files by date
            print dif_data
            for fn in dif_data:          
            
                fn2=fn
                print fn
                
                if not os.path.exists('/home/pi/Desktop/Pictures/'+fn.split('/')[-1][6:14]):
                    os.makedirs('/home/pi/Desktop/Pictures/'+fn.split('/')[-1][6:14])
                df=pd.read_csv(fn,sep=',',skiprows=7,parse_dates={'datet':[0]},index_col='datet',date_parser=parse2)#creat a new Datetimeindex
                df2=df
              
                try: 
                    index_good=np.where(abs(df2['Depth (m)'])<3) #Attention : If you want to use the angle, change the number under 1.
                    print index_good[0][3],index_good[0][-3]
                    index_good_start=index_good[0][3]
                    index_good_end=index_good[0][-3]
                except:
                    print "no good data"
                    os.system('sudo rm '+fn)
                    pass
                meantemp=round(np.mean(df['Temperature (C)'][index_good_start:index_good_end]),2)
                fig=plt.figure()
                ax1=fig.add_subplot(211)
                ax2=fig.add_subplot(212)
                df2['Depth (m)']=-1*df2['Depth (m)']# reverse the sign for plotting purposes
                time_df2=gmt_to_eastern(df2.index)
                ax2.plot(time_df2,df2['Depth (m)'],'b',label='Depth',color='green')
                ax2.legend()
                time_df=gmt_to_eastern(df.index)
                ax1.plot(time_df,df['Temperature (C)'],'b')
                ax1.set_ylabel('Temperature (Celius)')
                ax1.legend(['temp','in the water'])
                try:    
                        if max(df.index)-min(df.index)>Timedelta('0 days 04:00:00'):
                            ax1.xaxis.set_major_locator(dates.HourLocator(interval=(max(df.index)-min(df.index)).seconds/3600/6))# for hourly plot
                            ax1.xaxis.set_major_formatter(dates.DateFormatter('%D %H:%M'))
                            ax2.xaxis.set_major_formatter(dates.DateFormatter('%D %H:%M'))
                            
                        else: 
                            ax1.xaxis.set_major_locator(dates.MinuteLocator(interval=(max(df.index)-min(df.index)).seconds/60/6))# for minutely plot
                            ax1.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
                            ax2.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
                except:
                    print 'Not enough data to plot'

                ax1.text(0.9, 0.15, 'mean temperature in the water='+str(round(meantemp*1.8+32,1))+'F',
                            verticalalignment='bottom', horizontalalignment='right',
                            transform=ax1.transAxes,
                            color='green', fontsize=15)    
                ax1.set_xlabel('')
                ax1.set_xticklabels([])
                ax1.grid()
                ax12=ax1.twinx()
                ax12.set_title(tit)
                ax12.set_ylabel('Fahrenheit')
                ax12.set_xlabel('')
                ax12.set_xticklabels([])
                ax12.set_ylim(np.nanmin(df['Temperature (C)'].values)*1.8+32,np.nanmax(df['Temperature (C)'].values)*1.8+32)
                ax2=fig.add_subplot(212)
                ax2.plot(df2.index,df2['Depth (m)'].values,color='green')
                ax2.invert_yaxis()
                ax2.set_ylabel('depth(m)')
                ax2.set_ylim(np.nanmin(df2['Depth (m)'].values),np.nanmax(df2['Depth (m)'].values))
                ax2.set_ylim()
                ax2.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
                ax2.grid()
                ax22=ax2.twinx()
                ax22.set_ylabel('depth(feet)')
               
                ax22.set_ylim(np.nanmax(df2['Depth (m)'].values)*3.28084,np.nanmin(df2['Depth (m)'].values)*3.28084)        
                ax22.set_ylim()
                ax22.invert_yaxis()

                #ax2.xaxis.set_minor_locator(dates.HourLocator(interval=0)
                #ax2.xaxis.set_minor_formatter(dates.DateFormatter('%H'))
                #ax2.xaxis.set_major_locator(dates.DayLocator(interval=4))
                #ax2.xaxis.set_major_formatter(dates.DateFormatter('%D %H:%M'))
                plt.gcf().autofmt_xdate()    
                ax2.set_xlabel('Local TIME '+time_df[0].strftime('%m/%d/%Y %H:%M:%S')+' - '+time_df[-1].strftime('%m/%d/%Y %H:%M:%S'))
                print fn.split('/')[-1][2:12]
                plt.savefig('/home/pi/Desktop/Pictures/'+fn.split('/')[-1][6:14]+'/'+fn.split('/')[-1][15:21]+'.png')
                plt.close()
                print 'picture is saved'
                #os.system('sudo rm '+fn)
                #os.system('sudo rm '+fn2)
              
            #upfiles.extend(dif_data)
            a=open('uploaded_files/mypicfile.dat','r').close()
            
            a=open('uploaded_files/mypicfile.dat','a+')
            
            [a.writelines(i+'\n') for i in dif_data]
            a.close()
            
            

            print ' All Pictures are Generated'
            
            
                 
            return 
       
      except:
          return
                            
             
def wifi():
      if not os.path.exists('../uploaded_files'):
        os.makedirs('../uploaded_files')
      if not os.path.exists('../uploaded_files/myfile.dat'):
          open('../uploaded_files/myfile.dat','w').close()
      if 3>2:
            files=[]
            files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/*.csv')))
            #print files  
            with open('../uploaded_files/myfile.dat') as f:
                content = f.readlines()        
            upfiles = [line.rstrip('\n') for line in open('../uploaded_files/myfile.dat')]
            

            #f=open('../uploaded_files/myfile.dat', 'rw')
            dif_data=list(set(files)-set(upfiles))
            #print dif_data
            if dif_data==[]:
                print ''
                time.sleep(9)
                pass
         
            for u in dif_data:
                import time
                #print u
                session = ftplib.FTP('216.9.9.126','huanxin','123321')
                file = open(u,'rb') 
                session.cwd("/Matdata")  
                #session.retrlines('LIST')               # file to send
                session.storbinary("STOR "+u[24:], open(u, 'r'))   # send the file
                #session.close()
                session.quit()# close file and FTP
                time.sleep(1)
                file.close() 
                print u[24:]
                #os.rename('C:/Program Files (x86)/Aquatec/AQUAtalk for AQUAlogger/DATA/'+u[:7]+'/'+u[8:], 'C:/Program Files (x86)/Aquatec/AQUAtalk for AQUAlogger/uploaded_files/'+u[8:])
                print u[24:]+' uploaded'
                #os.rename(u[:7]+'/'+u[8:], "uploaded_files/"+u[8:]) 
                time.sleep(3)                     # close file and FTP
                f=open('../uploaded_files/myfile.dat','a+')
                #print 11111111111111111111111111111
                #print 'u:'+u
                f.writelines(u+'\n')
                f.close()
                
            #upfiles.extend(dif_data)
            #f=open('../uploaded_files/myfile.dat','w')
            #[f.writelines(i+'\n') for i in upfiles]
            #f.close()
            print 'all files are uploaded'
            #os.system('sudo ifdown wlan0')
            time.sleep(1500)
            return

       
      else:
            #import time
            #print 'no wifi'
            time.sleep(1)
            
            return

def judgement(boat_type,ma_file,t_file):
    valid='no'
    try:
        df=pd.read_csv(t_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)#creat a new Datetimeindex
        df2=pd.read_csv(ma_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse2)
        index_good=np.where(abs(df2['Az (g)'])<0.2)
        index_better=[]
        for e in range(len(index_good[0][:-1])):
                            if index_good[0][e+1]-index_good[0][e]>1:
                                index_better.append(index_good[0][e+1])
        print index_good,index_better
        if index_better==[]:
            index_better=[index_good[0][0]]

        index_good_start=index_better[-1]
        index_good_end=index_good[0][-1]+1
        print 'index_good_start:'+str(index_good_start)+' index_good_end:'+str(index_good_end)
        if boat_type=='lobster':
            if index_good_end-index_good_start<60:  #100 means 200 minutes
                print 'too less data, not in the sea'
                return valid,index_good_start,index_good_end
            else:
                valid='yes'
                return valid,index_good_start,index_good_end,
        else:
            if index_good_end-index_good_start<3:  #12 means 24 minutes
                print 'too less data, not in the sea'
                return valid,index_good_start,index_good_end 
            else:
                valid='yes'
                return valid,index_good_start,index_good_end           


    except:
        print 'data not in the sea'
        return valid,index_good_start,index_good_end

def judgement2(boat_type,s_file,logger_timerange_lim,logger_pressure_lim):
    valid='no'
    try:
        df=pd.read_csv(s_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)#creat a new Datetimeindex
        df2=pd.read_csv(s_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)
        index_good_start=1
        index_good_end=len(df)-1
        if boat_type=='lobster':
            if len(df)<40:  #100 means 100 minutes
                print 'too less data, not in the sea'
                return valid,index_good_start,index_good_end
            else:
                valid='yes'
                return valid,index_good_start,index_good_end
        else:
            index_good=np.where(abs(df2['Depth (m)'])>logger_pressure_lim)#make sure you change it before on the real boat
            #if len(index_good[0])<logger_timerange_lim or len(df2)>1440:  #make sure the good data is long enough,and total data is not more than one day  
            if len(index_good[0])<logger_timerange_lim or len(df2)>14400:  #make sure the good data is long enough,and total data is not more than one day  
                print 'too less data, not in the sea'
                return valid,index_good_start,index_good_end
            else:
                valid='yes'
                return valid,index_good[0][0],index_good[0][-1]           


    except:
        print 'data not in the sea'
        return valid,index_good_start,index_good_end


 
gpsd = None #seting the global variable
 
os.system('clear') #clear the terminal (optional)
 
class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
 






















        
