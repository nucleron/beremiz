# beremiz
Cloned http://dev.automforge.net/beremiz/ rev 7df108e8cb18

#Pre-requisites

## Ubuntu/Debian :
```bash
sudo apt-get install build-essential bison flex autoconf
sudo apt-get install python-wxgtk2.8 pyro mercurial
sudo apt-get install python-numpy python-nevow python-matplotlib python-lxml
```

#Prepare
```bash
mkdir ~/Beremiz
cd ~/Beremiz
```

#Get Source Code
```bash
cd ~/Beremiz
```
```bash
hg clone http://dev.automforge.net/beremiz
hg clone http://dev.automforge.net/matiec
```
or
```bash
git clone https://github.com/nucleron/beremiz.git
git clone https://github.com/nucleron/matiec.git
```

#Build MatIEC compiler
```bash
cd ~/Beremiz/matiec
autoreconf
./configure
make
```
#Build CanFestival (optional)

Only needed for CANopen support. Please read CanFestival manual to choose CAN interface other than 'virtual'.
```bash
cd ~/Beremiz
```
```bash
hg clone http://dev.automforge.net/CanFestival-3
```
or
```bash
git clone https://github.com/nucleron/CanFestival-3.git
```
```bash
cd ~/Beremiz/CanFestival-3
```
```bash
./configure --can=virtual
make
```

#Launch Beremiz
```bash
cd ~/Beremiz/beremiz
python Beremiz.py
```

#The End