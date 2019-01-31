'''
Author: Huanxin Xu,
Modified from Nick Lowell on 2016/12
version 0.0.30 update on 1/31/2019
15 remove linda marie from old AP3 list
For further questions ,please contact 508-564-8899, or send email to xhx509@gmail.com
Remember !!!!!!  Modify control file!!!!!!!!!!!!!
updates 
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
from subprocess import check_output
import psutil
from shutil import copyfile
from li_parse import parse_li
from wifiandpic import wifi,judgement2,parse,gps_compare
from func_readgps import func_readgps
logging.basicConfig()   #enable more verbose logging of errors to console
if not os.path.exists('/towifi'):
        os.makedirs('/towifi')
#################################### Time Sleep List#############################       
CONNECTION_INTERVAL = 1000  # Minimum number of seconds between reconnects
                                # Set to minutes for lab testing. Set to hours/days for field deployment.

CONNECTION_INTERVAL_After_success_data_transfer=1500
interval_before_program_run=400
scan_interval=6
habor_time_sleep_mobile=2500
habor_time_sleep_fixed=600
gps_reading_interval=90
interval_between_failed=1500

##################################################################################

LOGGING = False      #Enable log file for debugging Bluetooth COM errors. Deletes old log and creates new ble_log.txt for each connection.
#########################################################################################################################################
if 'r' in open('/home/pi/Desktop/mode.txt').read():
        file='control_file.txt'
        mode='real'
else:
        file='test_control_file.txt'
        mode='test'
f1=open(file,'r')
logger_timerange_lim=int(int(f1.readline().split('  ')[0])/1.5)
logger_pressure_lim=int(f1.readline().split('  ')[0])*1.8  #convert from fathom to meter
transmit=f1.readline().split('  ')[0]
MAC_FILTER=[f1.readline().split('  ')[0]]
boat_type=f1.readline().split('  ')[0]
vessel_num=f1.readline().split('  ')[0]
vessel_name=f1.readline().split('  ')[0]
tilt=f1.readline().split('  ')[0]
try:
        CONNECTION_INTERVAL=int(f1.readline().split('  ')[0])
except:
        pass
f1.close()
header_file=open('/home/pi/Desktop/header.csv','w')
header_file.writelines('Probe Type,Lowell\nSerial Number,'+MAC_FILTER[0][-5:]+'\nVessel Number,'+vessel_num+'\nVessel Name,'+vessel_name+'\nDate Format,YYYY-MM-DD\nTime Format,HH24:MI:SS\nTemperature,C\nDepth,m\n')   # create header with logger number
header_file.close()
print MAC_FILTER
scanner = btle.Scanner()    #defaut scan func
print mode
# A dictionary mapping mac address to last communication time. This should ultimately be moved
# to a file or database. This is a lightweight example.
last_connection = {}
index_times=0

try:
        file2=max(glob.glob('/home/pi/Desktop/gps_location/*'))
        os.system('sudo rm '+file2)
        time.sleep(2)
except:
        
        pass
func_readgps()  # We need to run function readgps twice to make sure we get at least two gps data in the gps file

if mode=='real' and boat_type=='mobile':
        time.sleep(interval_before_program_run)
else:
        time.sleep(1)
count_gps=0
func_readgps()  # We need to run function readgps twice to make sure we get at least two gps data in the gps file
while True:
    print('-'),
    
    try:
        
        wifi()
    except:
        time.sleep(1)
    try:
            
            file2=max(glob.glob('/home/pi/Desktop/gps_location/*'))
    except:
            func_readgps()
            time.sleep(15)
            func_readgps()
            time.sleep(1)
            file2=max(glob.glob('/home/pi/Desktop/gps_location/*'))
    try:
            df2=pd.read_csv(file2,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse,header=None)
            os.system('sudo timedatectl set-ntp 0')   # sync the real time
            os.system("sudo timedatectl set-time '"+str(df2.index[-1])+"'")
            time.sleep(1)
            os.system('sudo timedatectl set-ntp 1')
            if boat_type=='mobile':
                    if len(df2)>600:
                            os.system('sudo rm '+file2)
                            time.sleep(2)
                            func_readgps()
                            time.sleep(15)
                            func_readgps()
                  
    except:
            print 'something wrong with reading gps pulling file, comment that and next line after test'
            
            os.system('sudo rm '+file2)
            time.sleep(2)
            func_readgps()
            time.sleep(15)
            func_readgps()
    try:
            lat_1=float(df2[1][-1][:-1])
            lon_1=float(df2[2][-1][:-1])
    except:
            lat_1=9999.99
            lon_1=9999.99
    harbor_point_list=gps_compare(lat_1,lon_1,mode)
    if harbor_point_list<>[]:
            if boat_type=='mobile':
                    
                    print 'time sleep 3600'
                    time.sleep(habor_time_sleep_mobile)   # change to 3600 after test

            else:
                    print 'time sleep 600'
                    time.sleep(habor_time_sleep_fixed)
            os.system('sudo rm '+file2)
            func_readgps()
            time.sleep(15)
            func_readgps()
            continue
    #if boat_type=='mobile':
    index_times=index_times+1
    if index_times>=gps_reading_interval/7:
                    index_times=0
                    func_readgps()
    else:
            pass
    try:
            scan_list = scanner.scan(scan_interval)  # Scan for 6 seconds
    except:
            os.system('sudo reboot')
            


    # Get rid of everything that isn't a MAT1W
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
            time.sleep(2) # Delay 2 seconds to allow MLDP status string to clear

            # Make sure the clock is within range, otherwise sync it
            try:
                odlw_time = connection.get_time()
            except ValueError:
                print('ODL-1W returned an invalid time. Clock not checked.')
            else:
                # Is the clock more than a day off?
                if (datetime.datetime.now() - odlw_time).total_seconds() > 6:
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
            
            
            
            if not os.path.exists(folder):
                os.makedirs(folder)
            serial_num=folder[-5:].replace('-','')
            print serial_num
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
            file_names=glob.glob('/home/pi/Desktop/'+folder+'/*.lid')
            file_names.sort(key=os.path.getmtime)

            file_name=file_names[-1]
            print file_name


         
            file_num=datetime.datetime.now().strftime("%y%m%d_%H_%M")
        
            
            os.rename(file_name,'/home/pi/Desktop/'+folder+'/'+serial_num+'('+file_num+').lid')
           
            file_name='/home/pi/Desktop/'+folder+'/'+serial_num+'('+file_num+').lid'

            print file_name
            # Example - extract five-minute averaged temperature data from binary file
            print('Extracting 1.5-minute averaged temperature data...')
            try:
                    parse_li(file_name)  # default out_path
            except:
                    print "problems on parsing lid file"
                    time.sleep(900)
                    print "remove lid file in 100 seconds"
                    time.sleep(100)
                    os.system('sudo rm /home/pi/Desktop/'+folder+'/*.lid')
                    os.system('sudo reboot')
                    
            # Example - extract full resolution temperature data for Aug 4, 2014
            print('Extracting full resolution temperature data ')
            start = datetime.datetime(2011, 8, 1)  # create datetime objects for start and end time
            end = datetime.datetime(2030, 8, 3)
            
            s_file='/home/pi/Desktop/'+folder+'/'+serial_num+'('+file_num+')_S.txt'
            df=pd.read_csv(s_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)#creat a new Datetimeindex
            # To competible with logger to record every 60 seconds and 90 seconds
            try:
                    if str(df.index[-1]-df.index[-2])<'0 days 00:01:04':
                        time_sample_p=1.5
                        logger_timerange_lim=logger_timerange_lim*1.5
                        
                    else:
                        time_sample_p=1
            except:
                    time_sample_p=1
            os.rename(s_file,'/home/pi/Desktop/'+folder+'/'+serial_num+str(df.index[-1]).replace(':','')+'S.txt')
            new_file_path='/home/pi/Desktop/towifi/li_'+serial_num+'_'+str(df.index[-1]).replace(':','').replace('-','').replace(' ','_')#folder path store the files to uploaded by wifi
            
            s_file='/home/pi/Desktop/'+folder+'/'+serial_num+str(df.index[-1]).replace(':','')+'S.txt'
            try:

                        valid='no'  #boat type ,pick one from 'lobster' or 'mobile'
                        valid,st_index,end_index=judgement2(boat_type,s_file,logger_timerange_lim,logger_pressure_lim)
                        print 'valid is '+valid
            except:
                        print 'cannot read the s_file'
                    
            if valid=='yes':       
                if transmit=='yes':
                        
                        try:
                                
                                dft=df.ix[(df['Depth (m)']>0.85*max(df['Depth (m)']))]  # get rid of shallow data
                                if mode=='real':
                                    dft=dft.ix[2:]   #delay several minutes to let temperature sensor record the real bottom temp
                                if boat_type<>'fixed':
                                    dft=dft.ix[(dft['Temperature (C)']>mean(dft['Temperature (C)'])-3*std(dft['Temperature (C)'])) & (dft['Temperature (C)']<mean(dft['Temperature (C)'])+3*std(dft['Temperature (C)']))]
                                #a=df['Temperature (C)'].resample("D",how=['count','mean'],loffset=datetime.timedelta(hours=12))
                                #a.ix[a['count']<900,['mean']]='nan'
                                meantemp=str(int(round(np.mean(dft['Temperature (C)'][st_index:end_index]),2)*100)).zfill(4)
                                sdeviatemp=str(int(round(np.std(dft['Temperature (C)'][st_index:end_index]),2)*100)).zfill(4)
                                if   boat_type=='fixed':
                                        timerange=str(int((end_index-st_index)*1.5/60/time_sample_p)).zfill(3) #assumes logger time interval is 1.5 minutes,the result unit is in hours
                                else:
                                        timerange=str(int((end_index-st_index)*1.5/time_sample_p)).zfill(3) #logger time interval is 1.5 minutes put in hours
                                meandepth=str(abs(int(round(mean(dft['Depth (m)'].values))))).zfill(3)
                                rangedepth=str(abs(int(round(max(dft['Depth (m)'].values)-min(dft['Depth (m)'].values))))).zfill(3)
                                print 'meandepth'+meandepth+'rangedepth'+rangedepth+'timerange'+timerange+'temp'+meantemp+'sdev'+sdeviatemp+' logger name'+MAC_FILTER[0][-5:-3]+MAC_FILTER[0][-2:]
                                daily_ave=''
                                if boat_type=='fixed':
                                    tsod=dft.resample('D',how=['count','mean','median','min','max','std'],loffset=datetime.timedelta(hours=-12)) #creates daily averages,'-12' does not mean anything, only shows on datetime result 
                                    tsod=dft.resample('D',how=['mean'],loffset=datetime.timedelta(hours=-12))
                                    if len(tsod)>5:
                                        #temp5=[str(i).rjust(4,'f') for i in tsod.iloc[-5:]['Temperature (C)']['mean']]
                                        temp5=[str(int(round(float(i),2)*100)).zfill(4) for i in tsod.iloc[-6:-1]['Temperature (C)']['mean']]
                                        #tsod.ix[tsod['count']<minnumperday,['mean','median','min','max','std']] = 'NaN' # set daily averages to not-a-number if not enough went into it
                                    else:
                                        temp5=[str(int(round(float(i),2)*100)).zfill(4) for i in tsod.iloc[:-1]['Temperature (C)']['mean']]
                               
                                
                                    for i in temp5:
                                        daily_ave+=i
                                    print daily_ave
                                '''  
                                try:
                                        x=[p.pid for p in psutil.process_iter() if 'sudo' in str(p.name)]  #To terminate weather station program in background
                                        p1=psutil.Process(x[1])
                                        p1.terminate()
                                        print 'the weather station is closed '
                                except:
                                        print "no weather station is running in background"
                                '''
                                time.sleep(1)        
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
                                            old_ap3_boat=['mary_k','mystic']
                                            if vessel_name in old_ap3_boat:
                                                    ser.writelines('ylb9'+meandepth+rangedepth+timerange+meantemp+sdeviatemp+'eee'+MAC_FILTER[0][-5:-3]+MAC_FILTER[0][-2:]+daily_ave+'\n')
                                            else:
                                                    ser.writelines('ylb 9'+meandepth+rangedepth+timerange+meantemp+sdeviatemp+'eee'+MAC_FILTER[0][-5:-3]+MAC_FILTER[0][-2:]+daily_ave+'\n')
                                            time.sleep(2)
                                            print '999'+meandepth+rangedepth+timerange+meantemp+sdeviatemp+'eee'+MAC_FILTER[0][-5:-3]+MAC_FILTER[0][-2:]
                                            time.sleep(4)
                                            
                                            
                                            print 'good data, copy file to /home/pi/Desktop/towifi/'+serial_num+'('+file_num+')_T.txt'
                                except:
                                            print 'transmit error'
                                                            

                        except:
                                print 'no good data'
            if valid=='yes':
                    try:
                    
                            df1=df
                            df1.index.names=['datet(GMT)']
                            #file2=max(glob.glob('/home/pi/Desktop/gps_location/*'))
                            #df2=pd.read_csv(file2,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse,header=None)
                            lat=[]
                            lon=[]
                           
                            inx=str(min(df2.index,key=lambda d: abs(d-df1.index[0])))
                            for i in df1.index:
                                    try:
                                            if boat_type=='mobile':
                                                    
                                                    inx=str(min(df2[inx:].index,key=lambda d: abs(d-i)))
                                                    lat.append(float(df2[str(min(df2[inx:].index,key=lambda d: abs(d-i)))][1].values[0][:-1]))
                                                    lon.append(float(df2[str(min(df2[inx:].index,key=lambda d: abs(d-i)))][2].values[0][:-1]))
                                            else:
                                                    lat.append(lat_1)
                                                    lon.append(lon_1)
                                    except:
                                            print 'gps time is not matching the logger'
                                            time.sleep(1000)
                                            os.system('sudo reboot')
                            
                            
                            df1['lat']=lat
                            df1['lon']=lon
                            df1['HEADING']=['DATA' for i in range(len(df1))]      #add header DATA line
                            df1.reset_index(level=0,inplace=True)
                            df1.index=df1['HEADING']
                            df1=df1[['datet(GMT)','lat','lon','Temperature (C)','Depth (m)']]
                            print 'got the df'
                            print 'Parse accomplish'
                            
                            try:
                                if valid=='yes': #copy good file to 'towifi' floder 
                                        copyfile(file_name,new_file_path+'.lid')
                                       
                                        df1.to_csv(new_file_path+'_S1.csv')
                                        fh=open('/home/pi/Desktop/header.csv','r')
                                        content=fh.readlines()
                              
                                        file_saved=open(new_file_path+'.csv','w')
                                        [file_saved.writelines(i) for i in content]
                                        file_saved.close()
                                        os.system('cat '+new_file_path+'_S1.csv >> '+new_file_path+'.csv')
                                        os.system('rm '+new_file_path+'_S1.csv')
                                        print 'file cat finished'
                                        
                                else :
                                        
                                        os.remove(s_file) 
                            except:
                                print "Cannot copy or find the lid,MA or T file,cause no good data"

                    except:
                            print 'something wrong with gps pulling file'
            import time
            try:
                    os.system('sudo rm /home/pi/Desktop/'+folder+'/*.lid')
            except:
                    print 'no lid file'
            if valid=='yes':
                    print 'ok,all set'
                    os.system('sudo rm '+file2)
                    #os.remove(s_file)
                    time.sleep(2)
                    
                    
                    os.system('sudo reboot')
            else:
                    print 'time sleep 1500'
                    os.system('sudo rm '+file2)
                    
                    for l in range(interval_between_failed/88): # to make sure record gps every 90 seconds
                            time.sleep(88)
                            func_readgps()
                    print 'finished'        
                    
        except odlw_facade.Retries as error:  # this exception originates in odlw_facade
            print(str(error))
        except btle.BTLEException:  # only log time if the try block was successful
            print('Connection lost.')
        except odlw.XModemException as error:
            print(str(error))

