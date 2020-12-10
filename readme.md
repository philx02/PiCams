# Install on RPI
```bash
sudo apt-get install screen git
git clone https://github.com/philx02/PiCams.git
mkdir redirect
pushd redirect && ln -s ../PiCams/redirect.sh && ln -s ../PiCams/redirect.py && popd
```
Add this to `/etc/rc.local`:
```bash
su - pi -s /bin/bash -c "cd /home/pi/redirect && screen -d -S redirect -m ./redirect.sh"
```
