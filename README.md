# beremiz
Cloned http://dev.automforge.net/beremiz/ rev 7df108e8cb18

#Pre-requisites

## Ubuntu/Debian :
sudo apt-get install build-essential bison flex autoconf
sudo apt-get install python-wxgtk2.8 pyro mercurial
sudo apt-get install python-numpy python-nevow python-matplotlib python-lxml

#Prepare

mkdir ~/Beremiz
cd ~/Beremiz

#Get Source Code

cd ~/Beremiz

hg clone http://dev.automforge.net/beremiz

hg clone http://dev.automforge.net/matiec

or

git clone https://github.com/nucleron/beremiz.git

git clone https://github.com/nucleron/matiec.git

#Build MatIEC compiler

cd ~/Beremiz/matiec

autoreconf

./configure

make

#Build CanFestival (optional)

Only needed for CANopen support. Please read CanFestival manual to choose CAN interface other than 'virtual'.

cd ~/Beremiz

hg clone http://dev.automforge.net/CanFestival-3

or

git clone https://github.com/nucleron/CanFestival-3.git

cd ~/Beremiz/CanFestival-3

./configure --can=virtual

make

#Launch Beremiz

cd ~/Beremiz/beremiz

python Beremiz.py
