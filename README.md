turret
======

An app to operate a laptop and raspberry pi controlled gun turret.

laser\_service.py and laser.py run on the Raspberry Pi. They are used to control the laser.
In my setup, turret\_controller.py runs on a laptop connected to a webcam and makes RPC calls to the laser service running on the RPi.