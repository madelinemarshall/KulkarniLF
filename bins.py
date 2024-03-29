import sys 
import numpy as np
import individual
import imp
imp.reload(individual)
from individual import lf
import mosaic
import drawlf

qlumfiles = ['Data_new/dr7z2p2_sample.dat',
             #'Data_new/dr3z2p6_sample.dat', # This is DR3 not DR7 
             'Data_new/croom09sgp_sample.dat',
             'Data_new/croom09ngp_sample.dat',
             'Data_new/bossdr9color.dat',
             'Data_new/dr7z3p7_sample.dat',
             'Data_new/glikman11debug.dat',
             'Data_new/yang16_sample.dat',
             'Data_new/mcgreer13_dr7sample.dat',
             'Data_new/mcgreer13_s82sample.dat',
             'Data_new/mcgreer13_dr7extend.dat',
             'Data_new/mcgreer13_s82extend.dat',
             'Data_new/jiang16main_sample.dat',
             'Data_new/jiang16overlap_sample.dat',
             'Data_new/jiang16s82_sample.dat',
             'Data_new/willott10_cfhqsdeepsample.dat',
             'Data_new/willott10_cfhqsvwsample.dat',
             'Data_new/kashikawa15_sample.dat']

selnfiles = [('Selmaps_with_tiles/dr7z2p2_selfunc.dat', 6248.0, 13, r'Richards et al.\ 2006'),
             #('Selmaps_with_tiles/dr3z2p6_selfunc.dat', 1622.0, 13, r'Richards et al.\ 2006'), # This is DR3 not DR7! 
             ('Selmaps_with_tiles/croom09sgp_selfunc.dat', 64.2, 15, r'Croom et al.\ 2009'),
             ('Selmaps_with_tiles/croom09ngp_selfunc.dat', 127.7, 15, r'Croom et al.\ 2009'),
             ('Selmaps_with_tiles/ross13_selfunc2.dat', 2236.0, 1, r'Ross et al.\ 2013'),
             ('Selmaps_with_tiles/dr7z3p7_selfunc.dat', 6248.0, 13, r'Richards et al.\ 2006'),
             ('Selmaps_with_tiles/glikman11_selfunc_ndwfs.dat', 1.71, 6, r'Glikman et al.\ 2011'),
             ('Selmaps_with_tiles/glikman11_selfunc_dls.dat', 2.05, 6, r'Glikman et al.\ 2011'),
             ('Selmaps_with_tiles/yang16_sel.dat', 14555.0, 17, r'Yang et al.\ 2016'),
             ('Selmaps_with_tiles/mcgreer13_dr7selfunc.dat', 6248.0, 8, r'McGreer et al.\ 2013'),
             ('Selmaps_with_tiles/mcgreer13_s82selfunc.dat', 235.0, 8, r'McGreer et al.\ 2013'),
             ('Selmaps_with_tiles/jiang16main_selfunc.dat', 11240.0, 18, r'Jiang et al.\ 2016'),
             ('Selmaps_with_tiles/jiang16overlap_selfunc.dat', 4223.0, 18, r'Jiang et al.\ 2016'),
             ('Selmaps_with_tiles/jiang16s82_selfunc.dat', 277.0, 18, r'Jiang et al.\ 2016'),
             ('Selmaps_with_tiles/willott10_cfhqsdeepsel.dat', 4.47, 10, r'Willott et al.\ 2010'),
             ('Selmaps_with_tiles/willott10_cfhqsvwsel.dat', 494.0, 10, r'Willott et al.\ 2010'),
             ('Selmaps_with_tiles/kashikawa15_sel.dat', 6.5, 11, r'Kashikawa et al.\ 2015')]

method = 'Nelder-Mead'

zls = [(0.1, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0), (1.0, 1.2),
       (1.2, 1.4), (1.4, 1.6), (1.6, 1.8), (1.8, 2.2), (2.2, 2.4),
       (2.4, 2.5), (2.5, 2.6), (2.6, 2.7), (2.7, 2.8), (2.8, 2.9),
       (2.9, 3.0), (3.0, 3.1), (3.1, 3.2), (3.2, 3.3), (3.3, 3.4),
       (3.4, 3.5), (3.7, 4.1), (4.1, 4.7), (4.7, 5.5), (5.5, 6.5)]

lfs = [] 

for i, zl in enumerate(zls):

    lfi = lf(quasar_files=qlumfiles, selection_maps=selnfiles, zlims=zl)

    print('z =', zl)
    print('{:d} quasars in this bin.'.format(lfi.z.size))
    print('sids (samples): '+'  '.join(['{:2d}'.format(int(x)) for x in np.unique(lfi.sid)]))
    print('sids (maps): '+'  '.join(['{:2d}'.format(x.sid) for x in lfi.maps]))
    print(' ')
    
    g = (np.log10(1.e-6), -25.0, -3.0, -1.5)
    b = lfi.bestfit(g, method=method)

    zmin, zmax = zl 
    
    if zmin < 0.3:
        lfi.prior_min_values = np.array([-14.0, -32.0, -7.0, -10.0])
    else:
        lfi.prior_min_values = np.array([-14.0, -32.0, -7.0, -4.0])

    if zmin > 5.4:
        # Special priors for z = 6 data.
        lfi.prior_max_values = np.array([-4.0, -20.0, -4.0, 0.0])

        # Change result of optimize.minimize so that emcee works.
        lfi.bf.x[2] = -5.0
    elif zmin < 0.3:
        lfi.prior_max_values = np.array([-1.0, -15.0, 0.0, 15.0])
    else:
        lfi.prior_max_values = np.array([-4.0, -20.0, 0.0, 0.0])

    assert(np.all(lfi.prior_min_values < lfi.prior_max_values))
    
    lfi.run_mcmc()
    lfi.get_percentiles()

    drawlf.draw(lfi, show_individual_fit=True)
    
    WRITE_PARAMS = True
    if WRITE_PARAMS: 
        with open('bins.dat', 'a') as f:
            output = ([lfi.z.mean()] + list(zl) + lfi.phi_star
                      + lfi.M_star + lfi.alpha + lfi.beta)
            f.write(('{:.3f}  '*len(output)).format(*output)) 
            f.write('\n')
    
    lfs.append(lfi)

    # mosaic.draw(lfs)
