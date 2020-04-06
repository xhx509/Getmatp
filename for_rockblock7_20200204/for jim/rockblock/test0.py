#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  6 10:45:44 2020

@author: hxu
"""
'''
lat=41.789956
lon=-70.123445
depth=301
rangedepth=660
timelen=111
temp=1155
std_temp=1011
serial_num='3d7ade'

s=str(lat)+' '+str(lon)+' '+str(depth)+' '+str(rangedepth)+' '+str(timelen)+' '+str(temp)+' '+str(std_temp)+serial_num
print (s)


print (len(s))
a="".join("{:02x}".format(ord(c)) for c in s)
'''
#a=bytearray.fromhex(str(lat)+'33'+str(lon)+'33'+str(depth)+'33'+str(rangedepth)+'33'+str(temp)).decode()
a='343133342e323031372c373033372e313938352c30303130303030303232343935303032346565653761653631'
b=bytearray.fromhex(a).decode()
print (a)
print (b)
