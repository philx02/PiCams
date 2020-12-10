#!/bin/bash
raspivid -rot 180 -pf baseline -ih -t 0 -w 800 -h 600 -fps 15 -o - | python3 /home/pi/redirect/redirect.py 100000 spoluck.ca 5000
