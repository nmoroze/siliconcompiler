#!/bin/bash

sc -design heartbeat \
   -input "rtl verilog heartbeat.v" \
   -input "constraint sdc heartbeat.sdc" \
   -target "freepdk45_demo"
