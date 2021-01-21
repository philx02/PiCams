#!/bin/bash
raspivid -fps 25 -rot 180 -pf baseline -ih -t 0 -w 800 -h 600 -o - | python3 /home/pi/redirect/redirect.py 100000 spoluck.ca 5000
