import sys
import numpy as np 
from individual_mockData import lf
import drawlf

qlumfiles = ['Data_new/dr7z2p2_sample.dat',
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
             'Data_new/kashikawa15_sample.dat',
             'Data_new/giallongo15_sample.dat']

selnfiles = [('Data_new/dr7z2p2_selfunc.dat', 0.1, 0.05, 6248.0, 13, r'SDSS DR7 Richards et al.\ 2006'),
             ('Data_new/croom09sgp_selfunc.dat', 0.3, 0.05, 64.2, 15, r'2SLAQ Croom et al.\ 2009'),
             ('Data_new/croom09ngp_selfunc.dat', 0.3, 0.05, 127.7, 15, r'2SLAQ Croom et al.\ 2009'),
             ('Data_new/ross13_selfunc2.dat', 0.1, 0.05, 2236.0, 1, r'BOSS DR9 Ross et al.\ 2013'),
             ('Data_new/dr7z3p7_selfunc.dat', 0.1, 0.05, 6248.0, 13, r'SDSS DR7 Richards et al.\ 2006'),
             ('Data_new/glikman11_selfunc_ndwfs.dat', 0.05, 0.02, 1.71, 6, r'NDWFS+DLS Glikman et al.\ 2011'),
             ('Data_new/glikman11_selfunc_dls.dat', 0.05, 0.02, 2.05, 6, r'NDWFS+DLS Glikman et al.\ 2011'),
             ('Data_new/yang16_sel.dat', 0.1, 0.05, 14555.0, 17, r'SDSS+WISE Yang et al.\ 2016'),
             ('Data_new/mcgreer13_dr7selfunc.dat', 0.1, 0.05, 6248.0, 8, r'SDSS+S82 McGreer et al.\ 2013'),
             ('Data_new/mcgreer13_s82selfunc.dat', 0.1, 0.05, 235.0, 8, r'SDSS+S82 McGreer et al.\ 2013'),
             ('Data_new/jiang16main_selfunc.dat', 0.1, 0.05, 11240.0, 18, r'SDSS Jiang et al.\ 2016'),
             ('Data_new/jiang16overlap_selfunc.dat', 0.1, 0.05, 4223.0, 18, r'SDSS Jiang et al.\ 2016'),
             ('Data_new/jiang16s82_selfunc.dat', 0.1, 0.05, 277.0, 18, r'SDSS Jiang et al.\ 2016'),
             ('Data_new/willott10_cfhqsdeepsel.dat', 0.1, 0.025, 4.47, 10, r'CFHQS Willott et al.\ 2010'),
             ('Data_new/willott10_cfhqsvwsel.dat', 0.1, 0.025, 494.0, 10, r'CFHQS Willott et al.\ 2010'),
             ('Data_new/kashikawa15_sel.dat', 0.05, 0.05, 6.5, 11, r'Subaru Kashikawa et al.\ 2015'),
             ('Data_new/giallongo15_sel.dat', 0.0, 0.0, 0.047, 7, 'Giallongo et al.\ 2015')]

def lmd(lfg, zmin, zmax):
    
    method = 'Nelder-Mead'

    zl = (zmin, zmax)
    theta = lfg.bf.x
    lfi = lf(theta, lfg, quasar_files=qlumfiles, selection_maps=selnfiles, zlims=zl)
    print('{:d} quasars in this bin.'.format(lfi.z.size))

    g = (np.log10(1.e-6), -25.0, -3.0, -1.5)

    b = lfi.bestfit(g, method=method)
    print(b)

    lfi.prior_min_values = np.array([-14.0, -32.0, -10.0, -4.0])
    if zmin > 5.4:
        # Special priors for z = 6 data.
        lfi.prior_max_values = np.array([-4.0, -20.0, -4.0, 0.0])
        # Change result of optimize.minimize so that emcee works.
        lfi.bf.x[2] = -5.0
    else:
        lfi.prior_max_values = np.array([-4.0, -20.0, 0.0, 0.0])
    assert(np.all(lfi.prior_min_values < lfi.prior_max_values))

    lfi.run_mcmc()
    lfi.get_percentiles()

    # lfi.corner_plot()
    # lfi.chains()
    drawlf.draw(lfi)

    return lfi 
