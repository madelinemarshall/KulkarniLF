import numpy as np
import matplotlib as mpl
mpl.use('Agg') 
mpl.rcParams['text.usetex'] = True 
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = 'cm'
mpl.rcParams['font.size'] = '22'
import matplotlib.pyplot as plt
from astropy.stats import knuth_bin_width  as kbw
from astropy.stats import poisson_conf_interval as pci
from scipy.stats import binned_statistic as bs
from scipy.interpolate import interp1d
import cosmolopy.distance as cd
cosmo = {'omega_M_0':0.3,
         'omega_lambda_0':0.7,
         'omega_k_0':0.0,
         'h':0.7}

def volume(z, area, cosmo=cosmo):

    omega = (area/41253.0)*4.0*np.pi # str
    volperstr = cd.diff_comoving_volume(z,**cosmo) # cMpc^3 str^-1 dz^-1

    return omega*volperstr # cMpc^3 dz^-1

def binvol(m, zrange, bins, msel, psel, vsel, zsel):

    """
    
    Calculate volume in the i'th bin.

    """

    idx = np.searchsorted(bins, m)
    mlow = bins[idx-1]
    mhigh = bins[idx]

    dm = np.array([1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    # dz = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1.5, 1.5, 1.5])

    corr = np.loadtxt('Data_new/giallongo15_sel_correction.dat', usecols=(4,), unpack=True)

    total_vol = 0.0
    for i in range(msel.size):
        if (msel[i] >= mlow) and (msel[i] < mhigh):
            if (zsel[i] >= zrange[0]) and (zsel[i] < zrange[1]):
                total_vol += vsel[i]*psel[i]*dm[i]/corr[i]

    return total_vol

def get_lf(zrange, bins):

    z, m, p = np.loadtxt('Data_new/giallongo15_sample.dat', usecols=(1, 2, 3), unpack=True)
    select = ((z>=zrange[0]) & (z<zrange[1]))
    m = m[select]
    p = p[select]

    area = 0.047 # deg^2
    zsel, msel, psel = np.loadtxt('Data_new/giallongo15_sel.dat', usecols=(1, 2, 3), unpack=True)
    dz = zrange[1] - zrange[0]
    vol = volume(zsel, area)*dz

    psel[(zsel < zrange[0]) | (zsel >= zrange[1])] = 0.0

    v1 = np.array([binvol(x, zrange, bins, msel, psel, vol, zsel) for x in m])

    v1_nonzero = v1[np.where(v1>0.0)]
    m = m[np.where(v1>0.0)]

    h = np.histogram(m, bins=bins, weights=1.0/(v1_nonzero))

    nums = h[0]
    mags = (h[1][:-1] + h[1][1:])*0.5
    dmags = np.diff(h[1])*0.5

    left = mags - h[1][:-1]
    right = h[1][1:] - mags
    
    phi = nums
    logphi = np.log10(phi) # cMpc^-3 mag^-1

    n = np.histogram(m,bins=bins)[0]

    nlims = pci(n,interval='frequentist-confidence')
    nlims *= phi/n 
    uperr = np.log10(nlims[1]) - logphi 
    downerr = logphi - np.log10(nlims[0])

    return mags, left, right, logphi, uperr, downerr

def render(ax, zrange): 

    if zrange[0] < 4.5:
        ax.set_ylabel(r'$\log_{10}\left(\phi/\mathrm{cMpc}^{-3}\,\mathrm{mag}^{-1}\right)$')
    ax.set_xlabel('$M_{1450}$')


    ax.tick_params('both', which='major', length=7, width=1)
    ax.tick_params('both', which='minor', length=3, width=1)
    ax.tick_params('x', which='major', pad=6)

    sid = 7 

    # Plot binned LF from literature
    with open('Data/allqlfs.dat', 'r') as f:
        sample, z, m, m_lerr, m_uerr, phi, phi_lerr, phi_uerr = np.loadtxt(f, usecols=(1,2,6,7,8,9,10,11), unpack=True)
    select = ((sample==sid) & (z>=zrange[0]) & (z<zrange[1]))

    z = z[select]
    m = m[select]
    m_lerr = m_lerr[select]
    m_uerr = m_uerr[select]
    phi = phi[select]
    phi_lerr = phi_lerr[select]
    phi_uerr = phi_uerr[select]

    ax.scatter(m, phi, c='r', label='Giallongo et al.\ 2015', edgecolor='None', zorder=303, s=32) 
    ax.errorbar(m, phi, ecolor='r', capsize=0,
                xerr=np.vstack((m_lerr, m_uerr)),
                yerr=np.vstack((phi_lerr, phi_uerr)), fmt='None', zorder=304)

    # Plot our binning
    bins = np.array([-23.5, -21.5, -20.5, -19.5, -18.5])

    mags, left, right, logphi, uperr, downerr = get_lf(zrange, bins)
    print(zrange)
    print(mags)
    print(10.0**(phi-logphi[-len(phi):]))

    ax.scatter(mags, logphi, c='g', edgecolor='None', zorder=306, label='my binning', s=35)
    ax.errorbar(mags, logphi, ecolor='g', capsize=0,
                xerr=np.vstack((left, right)),
                yerr=np.vstack((uperr, downerr)),
                fmt='None',zorder=306)

    ax.set_xlim(-24.0, -16.0)
    ax.set_ylim(-7.0, -3.0)
    plt.xticks(np.arange(-24,-15,2))
    plt.yticks(np.arange(-7,-2,1))
    if zrange[0] > 4.0:
        ax.set_yticklabels('')
        ax.get_xticklabels()[0].set_visible(False)

    plottitle = r'${:g}\leq z<{:g}$'.format(zrange[0], zrange[1]) 
    plt.title(plottitle, size='medium', y=1.01)

    if zrange[0] > 4.5:
        plt.legend(loc='lower right', fontsize=10, handlelength=3, frameon=False, framealpha=0.0,
                   labelspacing=.1, handletextpad=-0.4, borderpad=0.6, scatterpoints=1)

    return 
    
def draw():

    nplots_x = 3
    nplots_y = 1
    nplots = nplots_x * nplots_y

    plot_number = 0

    nx = nplots_x
    ny = nplots_y 
    factor_x = 3.0
    factor_y = 4.0
    ldim = 0.33*factor_x
    bdim = 0.25*factor_y
    rdim = 0.1*factor_x
    tdim = 0.1*factor_y
    wspace = 0.
    hspace = 0. 

    plotdim_x = factor_x*nx + (nx-1)*wspace
    plotdim_y = factor_y*ny + (ny-1)*hspace

    hdim = plotdim_x + ldim + rdim 
    vdim = plotdim_y + tdim + bdim 

    fig = plt.figure(figsize=(hdim, vdim), dpi=100)

    l = ldim/hdim
    b = bdim/vdim
    r = (ldim + plotdim_x)/hdim
    t = (bdim + plotdim_y)/vdim 
    fig.subplots_adjust(left=l, bottom=b, right=r, top=t, wspace=wspace/hdim,
                        hspace=hspace/vdim)

    ax = fig.add_subplot(nplots_y, nplots_x, 1)
    render(ax, (4.0, 4.5))

    ax = fig.add_subplot(nplots_y, nplots_x, 2)
    render(ax, (4.5, 5.0))
    
    ax = fig.add_subplot(nplots_y, nplots_x, 3)
    render(ax, (5.0, 6.5))

    plt.savefig('giallongo.pdf')

    #plt.close('all')

draw()

