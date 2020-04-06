#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 13:49:16 2020

@author: hxu
"""
import requests

url = 'http://studentdrifters.org/posthuanxin/post.php'
myobj = {'somekey': 'somevalue'}

x = requests.post(url, data = myobj)

#print the response text (the content of the requested file):

print(x.text)
