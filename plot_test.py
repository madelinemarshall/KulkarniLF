import sys
import numpy as np 
from individual import lf
import drawlf

import matplotlib.pyplot as plt

    

fig,ax=plt.subplots(1,1)
ax.plot([0,0],[1,1])#draw(lfi, ax, show_individual_fit=True)
plt.savefig('TEST.pdf')
plt.show()

