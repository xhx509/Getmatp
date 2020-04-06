#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 12:41:15 2020

@author: hxu
"""

import requests
response = requests.get('https://docs.google.com/spreadsheets/d/1uLhG_q09136lfbFZppU2DU9lzfYh0fJYsxDHUgMB1FM/edit#gid=0&output=csv')
assert response.status_code == 200, 'Wrong status code'
print(response.content)