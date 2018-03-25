'''
Author: Huanxin Xu,
Modified from Nick Lowell on 2016/12
version 0.0.9 2018/03/25 where previous versions are documented in the "getmatp_changes" googglesheet
Add vessel number ,get rid of 't','ma' file. improve ploting, convert psi to depth meter in
          getmap.py and control_file.txt
For further questions ,please contact 508-564-8899, or send email to xhx509@gmail.com
Remember !!!!!!  Modify control file!!!!!!!!!!!!! 
'''




import sys
sys.path.insert(1, '/home/pi/Desktop/mat_modules')
import odlw_facade
import odlw
import bluepy.btle as btle
import time
import datetime
import numpy as np
import pandas as pd
import serial
import os
from pandas import read_csv
from pylab import mean, std
import OdlParsing
import glob
import logging
from shutil import copyfile
from li_parse import parse_li
from wifiandpic import p_create_pic,wifi,judgement2,parse
from func_readgps import func_readgps
logging.basicConfig()   #enable more verbose logging of errors to console
if not os.path.exists('/towifi'):
        os.makedirs('/towifi')
CONNECTION_INTERVAL = 30  # Minimum number of seconds between reconnects
                                # Set to minutes for lab testing. Set to hours/days for field deployment.
                                
LOGGING = False      #Enable log file for debugging Bluetooth COM errors. Deletes old log and creates new ble_log.txt for each connection.
#########################################################################################################################################

file='control_file.txt'
f1=open(file,'r')
logger_timerange_lim=int(f1.readline().split('  ')[0]) # what is the difference between this and the hardcoded "connection_interval"?
logger_pressure_lim=int(f1.readline().split('  ')[0]) # minimum pressure in what units to accept data
transmit=f1.readline().split('  ')[0]
MAC_FILTER=[f1.readline().split('  ')[0]]
boat_type=f1.readline().split('  ')[0]
vessel_num=f1.readline().split('  ')[0]
f1.close()
header_file=open('/home/pi/Desktop/header.csv','w')
header_file.writelines('Probe Type,Lowell\nSerial Number,'+MAC_FILTER[0][-5:]+'\nVessel Number,'+vessel_num+'\nDate Format,YYYY-MM-DD\nTime Format,HH24:MI:SS\nTemperature,C\nDepth,m\n')   # create header with logger number
header_file.close() #why not add vessel_name in the header as well and do we want to distinquish header lines from DATA lines? 
print MAC_FILTER
scanner = btle.Scanner() # what does this command do?  Turns on the bluetooth?

# A dictionary mapping mac address to last communication time. This should ultimately be moved
# to a file or database. This is a lightweight example.
last_connection = {}
index_times=0
func_readgps()  # We need to run function readgps twice to make sure we get at least two gps data in the gps file
func_readgps()  # We need to run function readgps twice to make sure we get at least two gps data in the gps file
while True:
    print('-'),
    
    try:   
        wifi()
    except:
        time.sleep(1)
    index_times=index_times+1
    if index_times>=14: # does this mean you get a new GPS every 14 seconds?
            index_times=0
            func_readgps()
            
    scan_list = scanner.scan(6)  # Scan for 6 seconds

            


    # Get rid of everything that isn't a MAT1W or MATP
    scan_list =[device for device in scan_list if device.addr in MAC_FILTER]

    # Prefer new connections, then the oldest connection
    oldest_connection = time.time()
    mac = None
    for dev in scan_list:
        if dev.addr not in last_connection:
            mac = dev.addr
            break
        if last_connection[dev.addr] < oldest_connection and \
                                time.time() - last_connection[dev.addr] > CONNECTION_INTERVAL:
            mac, oldest_connection = dev.addr, last_connection[dev.addr]

    if not mac:
        continue
    print('')
    print('*************New Connection*************')
    print time.strftime("%c")
    print('Connecting to {}'.format(mac))
    
    try:
        p = btle.Peripheral(mac)  # create a peripheral object. This opens a BLE connection.
    except btle.BTLEException:  # There was a problem opening the BLE connection.
        print('Failed to connect to ' + mac)
        continue

    if LOGGING:             #Debug Code.Creating a log file that saves ALL coms for the current connection. Sometimes helpful for troubleshooting.
        file_h = open('ble_log.txt', 'w')  # This is bad form but temporary
        log_obj = odlw_facade.BLELogger(file_h)


    with p:
        try:  # all commands need to be in the try loop. This will catch dropped connections and com errors
            connection = odlw_facade.OdlwFacade(p)  # create a facade for easy access to the ODLW

            if LOGGING:
                connection.enable_logging(log_obj)

            time.sleep(1)   # add a short delay for unknown, but required reason

            # Stop the logger from collecting data to improve reliability of comms and allow data transfer
            print ('Stopping deployment: ' + connection.stop_deployment())
            time.sleep(2)   # delay 2 seconds to allow files to close on SD card

            #Increase the BLE connection speed
            print('Increasing BLE speed.')
            connection.control_command('T,0006,0000,0064')  #set latency and timeouts in RN4020 to minimums

            # Make sure the clock is within range, otherwise sync it
            try:
                odlw_time = connection.get_time()
            except ValueError:
                print('ODL-1W returned an invalid time. Clock not checked.')
            else:
                # Is the clock more than a day off?  Looks like you are actually checking 10 seconds not a full day.
                if (datetime.datetime.now() - odlw_time).total_seconds() > 10:
                    print('did  Syncing time.')
                    connection.sync_time()

            # Filler commands to test querying
            # for i in range(1):
            #     print('Time: ' + str(connection.get_time()))
            #     print('Status: ' + connection.get_status())
            #     print('Firmware: ' + connection.get_firmware_version())
            #     print('Serial Number: ' + connection.get_serial_number())

            # Download any .lis files that aren't found locally
            folder = mac.replace(':', '-').lower()  # create a subfolder with the ODL-1W's unique mac address
            serial_num=folder[-2:]
            if not os.path.exists(folder):
                os.makedirs(folder)

            print('Requesting file list')
            files = connection.list_files()  # get a list of files on the ODLW
            files.reverse()
            print files         #Note: ODL-W has a very limited file system. Microprocessor will become RAM bound if files are over 55-65.
                                #The exact number depends on file name length and ???. TBD: add a check for files numbers above 55.

            for name, size in files:

                if not name.endswith('.lid'):
                    continue
                # Check if the file exists and get it's size
                file_path = os.path.join(folder, name)
                local_size = None
                if os.path.isfile(file_path):
                    local_size = os.path.getsize(file_path)

                if not local_size or local_size != size:
                    with open(file_path, 'wb') as outstream:
                        print('Downloading ' + name)
                        start_time = time.time()
                        connection.get_file(name, size, outstream)
                        end_time = time.time()
                        print('Download of {} complete - {:0.2f} bytes/sec.'.format(name, size/(end_time-start_time)))
                    print('Deleting {}'.format(name))
                    connection.delete_file(name)

                else:
                    print('Deleting {}'.format(name))
                    connection.delete_file(name)

            print('Restarting Logger: ' + connection.start_deployment())
            time.sleep(2) #2 second delay to write header of new data file
            last_connection[mac] = time.time()  # keep track of the time of the last communication
            print('Disconnecting')
            file_names=glob.glob('/home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/*.lid')
            file_names.sort(key=os.path.getmtime)

            file_name=file_names[-1]
            #file_name2=file_names2[-1]
            print file_name


            #file_num =str(max(nums)+1)
            file_num=datetime.datetime.now().strftime("%y%m%d_%H_%M")
        
            
            os.rename(file_name,'/home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/'+serial_num+'('+file_num+').lid')
           
            file_name='/home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/'+serial_num+'('+file_num+').lid'

            print file_name
            # Example - extract five-minute averaged temperature data from binary file
            print('Extracting five-minute averaged temperature data...')
            try:
                    parse_li(file_name)  # default out_path
            except:
                    print "problems on parsing lid file"
                    time.sleep(900)
                    print "remove lid file in 100 seconds"
                    time.sleep(100)
                    os.system('sudo rm /home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/*.lid')
                    
            # Example - extract full resolution temperature data for Aug 4, 2014
            print('Extracting full resolution temperature data ')
            start = datetime.datetime(2011, 8, 1)  # create datetime objects for start and end time
            end = datetime.datetime(2030, 8, 3)
            
            s_file='/home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/'+serial_num+'('+file_num+')_S.txt'
            df=pd.read_csv(s_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)#creat a new Datetimeindex

            # what are you doing in the next three lines?  Are you just making a copy of the S.txt file?
            os.rename(s_file,'/home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/'+serial_num+str(df.index[-1]).replace(':','')+'S.txt')
            new_file_path='/home/pi/Desktop/towifi/li_'+serial_num+'_'+str(df.index[-1]).replace(':','').replace('-','').replace(' ','_')#folder path store the files to uploaded by wifi
            s_file='/home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/'+serial_num+str(df.index[-1]).replace(':','')+'S.txt'
            
            if len(df)>1000:
                        
                        os.remove(s_file)
                        print 'data is more than one day, delete assuming that this is not a fixed gear application'
                        time.sleep(1800)
                        os.system('sudo rm /home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/*.lid')
                        os.system('sudo reboot')
                       
            df1=pd.read_csv(s_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)
            df1.index.names=['datet(GMT)']
            file2=max(glob.glob('/home/pi/Desktop/gps_location/*'))
            column_name=['lat','lon'] # where do you use "column_name"?  Can we delete this line?
            df2=pd.read_csv(file2,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse,header=None)
            lat=[]
            lon=[]
           
            inx=str(min(df2.index,key=lambda d: abs(d-df1.index[0])))
            for i in df1.index:
                    try:
                            inx=str(min(df2[inx:].index,key=lambda d: abs(d-i)))
                            lat.append(df2[str(min(df2[inx:].index,key=lambda d: abs(d-i)))][1].values[0])
                            lon.append(df2[str(min(df2[inx:].index,key=lambda d: abs(d-i)))][2].values[0])
                    except:
                            print 'gps time is not matching the logger'
                            time.sleep(1000)
                            os.system('sudo reboot')
            
            
            df1['lat']=lat
            df1['lon']=lon
            df1=df1[['lat','lon','Temperature (C)','Depth (m)']]
            print 'got the df'
            print 'Parse accomplish'
            
            try:
                valid='no'
                boat_type='fishing'  #boat type ,pick one from 'lobster' or 'fish' The should be "mobile" or "fixed".
                valid,st_index,end_index=judgement2(boat_type,s_file,logger_timerange_lim,logger_pressure_lim)
                print 'valid is '+valid
                if valid=='yes': #copy good file to 'towifi' floder 
                        copyfile(file_name,new_file_path+').lid')
                       
                        df1.to_csv(new_file_path+'_S1.csv')
                        fh=open('/home/pi/Desktop/header.csv','r')
                        content=fh.readlines()
              
                        file_saved=open(new_file_path+'.csv','w')
                        [file_saved.writelines(i) for i in content]
                        file_saved.close()
                        os.system('cat '+new_file_path+'_S1.csv >> '+new_file_path+'.csv')# Concantenated monthly file?
                        os.system('rm '+new_file_path+'_S1.csv')
                        print 'file cat finished'
                        #copyfile(s_file,new_file_path+'_S.txt')
                else :
                        
                        os.remove(s_file)
                        
                        

                
                
                
                
            except:
                print "Cannot copy or find the lid,cause no good data"
            if valid=='yes':       
                if transmit=='yes':
                        
                        try:
                                #df=pd.read_csv(new_file_path+'_P.txt')
                                df=df.ix[(df['Depth (m)']>0.85*mean(df['Depth (m)']))]  # get rid of shallow data
                                dft=df
                                #dft=pd.read_csv(new_file_path+'_T.txt')
                                # gets rid of spikes > 3 std from the mean?
                                dft=dft.ix[(dft['Temperature (C)']>mean(dft['Temperature (C)'])-3*std(dft['Temperature (C)'])) & (dft['Temperature (C)']<mean(dft['Temperature (C)'])+3*std(dft['Temperature (C)']))]
                                
                                maxtemp=str(int(round(max(dft['Temperature (C)'][st_index:end_index]),2)*100))
                                # to reduce code below, you should consider using Python string.zfill(X) where "X" is the desired number of characaters you want 
                                if len(maxtemp)<4:
                                            maxtemp='0'+maxtemp
                                mintemp=str(int(round(min(dft['Temperature (C)'][st_index:end_index]),2)*100))
                                if len(mintemp)<4:
                                            mintemp='0'+mintemp
                                meantemp=str(int(round(np.mean(dft['Temperature (C)'][st_index:end_index]),2)*100))
                                if len(meantemp)<3:
                                            meantemp='0'+meantemp
                                sdeviatemp=str(int(round(np.std(dft['Temperature (C)'][st_index:end_index]),2)*100))
                                for k in range(4):
                                          if len(sdeviatemp)<4:
                                            sdeviatemp='0'+sdeviatemp
                                timerange=str(int(end_index-st_index))
                                #time_len=str(int(round((df['yd'][-1]-df['yd'][0]),3)*1000))
                                for k in range(3):
                                        if len(timerange)<3:
                                            timerange='0'+timerange
                                    
                                    # meandepth
                                meandepth=str(abs(int(round(mean(df['Depth (m)'].values)))))
                                #print (mean(df['Pressure (psia)'].values)-13.89)/1.457
                                for k in range(3):
                                        if len(meandepth)<3:
                                            meandepth='0'+meandepth
                                    
                                    # meantemp
                                meantemp=str(int(round(mean(dft['Temperature (C)'].values),2)*100))
                                if len(meantemp)<4:
                                        meantemp='0'+meantemp
                                    
                                    # rangedepth
                                rangedepth=str(abs(int(round(max(df['Depth (m)'].values)-min(df['Depth (m)'].values)))))
                                #print (max(df['Pressure (psia)'].values)-min(df['Pressure (psia)'].values))/1.457
                                for k in range(3):
                                        if len(rangedepth)<3:
                                            rangedepth='0'+rangedepth
                                print 'meandepth'+meandepth+'rangedepth'+rangedepth+'timerange'+timerange+'temp'+meantemp+'sdev'+sdeviatemp
                                try:
                                     
                                            ports='tty-huanxintrans'
                                            ser=serial.Serial('/dev/'+ports, 9600)                #   in Linux
                                            time.sleep(2)
                                            ser.writelines('\n')
                                            print 111
                                            time.sleep(2)
                                            ser.writelines('\n')
                                            print 222
                                            time.sleep(2)
                                            ser.writelines('\n')
                                            time.sleep(2)
                                            ser.writelines('i\n')
                                            print 333
                                            time.sleep(3)
                                            #ser.writelines('ylb00E'+maxtemp+'D'+mintemp+'C'+meantemp+'B'+sdeviatemp+'0000000000000000000000000000000000000000000000\n')
                                            ser.writelines('ylb9'+meandepth+rangedepth+timerange+meantemp+sdeviatemp+'\n')
                                            time.sleep(2)
                                            print '999'+meandepth+rangedepth+timerange+meantemp+sdeviatemp
                                            time.sleep(4)
                                            
                                            #copyfile(ma_file,'/home/pi/Desktop/towifi/'+serial_num+'('+file_num+')_MA.txt')
                                            #copyfile(t_file,'/home/pi/Desktop/towifi/'+serial_num+'('+file_num+')_T.txt')
                                            print 'good data, copy file to /home/pi/Desktop/towifi/'+serial_num+'('+file_num+')_T.txt'
                                except:
                                            print 'transmit error'
                                                            

                        except:
                                print 'no good data'
            
            import time
            os.system('sudo rm /home/pi/Desktop/00-1e-c0-3d-7a-'+serial_num+'/*.lid')
            if valid=='yes':
                    print 'ok,all set'
                    os.system('sudo rm '+file2)
                    time.sleep(1)
                    
                    #print 'time sleep 1000'
                    
                    os.system('sudo reboot')
                    #time.sleep(1000)
            else:
                    print 'time sleep 1500'
                    for l in range (17):
                            time.sleep(89)
                            func_readgps()
                            
                    
        except odlw_facade.Retries as error:  # this exception originates in odlw_facade
            print(str(error))
        except btle.BTLEException:  # only log time if the try block was successful
            print('Connection lost.')
        except odlw.XModemException as error:
            print(str(error))

