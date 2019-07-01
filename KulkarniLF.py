import sys
import numpy as np 
from individual import lf
import drawlf
import matplotlib.pyplot as plt

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
             'Data_new/kashikawa15_sample.dat']
             #'Data_new/giallongo15_sample.dat']
qlumfiles=['/home/mmarshal/simulation_codes/data/KulkarniQLF/'+name for name in qlumfiles]

path='/home/mmarshal/simulation_codes/data/KulkarniQLF/'
selnfiles = [(path+'Selmaps_with_tiles/dr7z2p2_selfunc.dat',
              6248.0, 13,
              r'SDSS DR7 Richards et al.\ 2006'),
             
             (path+'Selmaps_with_tiles/croom09sgp_selfunc.dat',
              64.2, 15,
              r'2SLAQ Croom et al.\ 2009'),
             
             (path+'Selmaps_with_tiles/croom09ngp_selfunc.dat',
              127.7, 15,
              r'2SLAQ Croom et al.\ 2009'),
             
             (path+'Selmaps_with_tiles/ross13_selfunc2.dat',
              2236.0, 1,
              r'BOSS DR9 Ross et al.\ 2013'),
             
             (path+'Selmaps_with_tiles/dr7z3p7_selfunc.dat',
              6248.0, 13,
              r'SDSS DR7 Richards et al.\ 2006'),
             
             (path+'Selmaps_with_tiles/glikman11_selfunc_ndwfs.dat',
               1.71, 6,
              r'NDWFS+DLS Glikman et al.\ 2011'),
             
             (path+'Selmaps_with_tiles/glikman11_selfunc_dls.dat',
               2.05, 6,
              r'NDWFS+DLS Glikman et al.\ 2011'),
             
             (path+'Selmaps_with_tiles/yang16_sel.dat',
              14555.0, 17,
              r'SDSS+WISE Yang et al.\ 2016'),
             
             (path+'Selmaps_with_tiles/mcgreer13_dr7selfunc.dat',
              6248.0, 8,
              r'SDSS DR7 McGreer et al.\ 2013'),
             
             (path+'Selmaps_with_tiles/mcgreer13_s82selfunc.dat',
              235.0, 8,
              r'S82 McGreer et al.\ 2013'),
             
             (path+'Selmaps_with_tiles/jiang16main_selfunc.dat',
              11240.0, 18,
              r'SDSS Jiang et al.\ 2016'),
             
             (path+'Selmaps_with_tiles/jiang16overlap_selfunc.dat',
              4223.0, 18,
              r'SDSS Jiang et al.\ 2016'),
             
             (path+'Selmaps_with_tiles/jiang16s82_selfunc.dat',
              277.0, 18,
              r'SDSS Jiang et al.\ 2016'),
             
             (path+'Selmaps_with_tiles/willott10_cfhqsdeepsel.dat',
               4.47, 10,
              r'CFHQS Willott et al.\ 2010'),
             
             (path+'Selmaps_with_tiles/willott10_cfhqsvwsel.dat',
               494.0, 10,
              r'CFHQS Willott et al.\ 2010'),
             
             (path+'Selmaps_with_tiles/kashikawa15_sel.dat',
               6.5, 11,
              r'Subaru Kashikawa et al.\ 2015')]
             
             # ('Selmaps_with_tiles/giallongo15_sel.dat',
             #  0.0, 0.0, 0.047, 7,
             #  'Giallongo et al.\ 2015')]


def draw(lf, ax, composite=None, showMockSample=False, show_individual_fit=True):

    """

    Plot data, best fit LF, and posterior LFs.

    """

    z_plot = lf.z.mean() 
    
    #fig = plt.figure(figsize=(7, 7), dpi=100)
    #ax = fig.add_subplot(1, 1, 1)
    #ax.tick_params('both', which='major', length=7, width=1)
    #ax.tick_params('both', which='minor', length=3, width=1)

    drawlf.render(ax, lf, composite=composite, showMockSample=showMockSample,
           show_individual_fit=show_individual_fit)

    #ax.set_xlim(-17.0, -31.0)
    #ax.set_ylim(-12.0, -4.0)
    #ax.set_xticks(np.arange(-31,-16, 2))

    #ax.set_xlabel(r'$M_{1450}$')
    #ax.set_ylabel(r'$\log_{10}\left(\phi/\mathrm{cMpc}^{-3}\,\mathrm{mag}^{-1}\right)$')

    legend_title = r'$\langle z\rangle={0:.3f}$'.format(z_plot)
    plt.legend(loc='lower left', fontsize=12, handlelength=3,
               frameon=False, framealpha=0.0, labelspacing=.1,
               handletextpad=0.1, borderpad=0.2, scatterpoints=1,
               title=legend_title)

    #plottitle = r'${:g}\leq z<{:g}$'.format(lf.zlims[0], lf.zlims[1]) 
    #plt.title(plottitle, size='medium', y=1.01)
    #plt.show()
    #plotfile = dirname+'lf_z{0:.3f}.pdf'.format(z_plot)
    #plt.savefig(plotfile, bbox_inches='tight')

    #plt.close('all') 
    return 
   
 
def plot_Kulkarni(zmin,zmax,ax,num_runs=1000):
  method = 'Nelder-Mead'

  zl = (zmin, zmax) 
  lfi = lf(quasar_files=qlumfiles, selection_maps=selnfiles, zlims=zl)

  g = (np.log10(1.e-6), -25.0, -3.0, -1.5)

  b = lfi.bestfit(g, method=method)

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
    
  lfi.run_mcmc(num_runs)
  bf = np.median(lfi.samples, axis=0)

  lfi.get_percentiles()

  #lfi.chains()
  #lfi.corner_plot()

  draw(lfi, ax, show_individual_fit=True)
  return lfi


if __name__=='__main__':
  zmin = float(sys.argv[1])
  zmax = float(sys.argv[2])

  fig,ax=plt.subplots(1,1)
  plot_Kulkarni(zmin,zmax,ax)  
  plt.savefig('TEST.pdf')
  plt.show()

