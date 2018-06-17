import pynortek
import pylab as pl
DPATH='/home/holterma/holterma.owncloud.io-warnemuende.de/Documents/cruises/2018_EMB184/deployments/CTD/Aquadopp/'
deployment = 'C7_119'
aq = pynortek.pynortek(DPATH + deployment)


ed = '/home/holterma/Dokumente/EMB177/moorings/eddy/vector/EDDYT12'
eddy = pynortek.pynortek(ed)



pl.figure(1)
pl.clf()
pl.pcolor(aq.t,aq.data['dis_beam'],aq.data['v1'].T)


pl.draw()
pl.show()
