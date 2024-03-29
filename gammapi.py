import numpy as np 
import matplotlib as mpl
#mpl.use('Agg') 
mpl.rcParams['text.usetex'] = True 
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = 'cm'
mpl.rcParams['font.size'] = '22'
import matplotlib.pyplot as plt
import rtg 
from scipy.optimize import curve_fit
import fit_emissivity
import matplotlib.patches as mpatches

def luminosity(M):
    return 10.0**((51.60-M)/2.5) # ergs s^-1 Hz^-1 


def f(loglf, theta, M, z, fit='composite'):
    # SED power law index is from Beta's paper.
    L = luminosity(M)
    if fit=='individual':
        # If this gammapi calculation is for an individual fit (in,
        # say, fitlf.py) then loglf might not have any z argument.
        return (10.0**loglf(theta, M))*L*((912.0/1450.0)**0.61)
    return (10.0**loglf(theta, M, z))*L*((912.0/1450.0)**0.61)
        

def emissivity(loglf, theta, z, mlims, fit='composite'):
    # mlims = (lowest magnitude, brightest magnitude)
    #       = (brightest magnitude, faintest magnitude)
    m = np.linspace(mlims[0], mlims[1], num=1000)
    if fit=='individual':
        farr = f(loglf, theta, m, z, fit='individual')
    else:
        farr = f(loglf, theta, m, z)
    return np.trapz(farr, m) # erg s^-1 Hz^-1 Mpc^-3


def get_emissivity(lfi, z, Mfaint=-18.0):

    rindices = np.random.randint(len(lfi.samples), size=300)
    e = np.array([emissivity(lfi.log10phi, theta, z, (-30.0, Mfaint), fit='individual')
                          for theta
                          in lfi.samples[rindices]])
    l = np.percentile(e, 15.87) 
    u = np.percentile(e, 84.13)
    c = np.mean(e)
    lfi.emissivity = [u, l, c]

    return 


def f_1450(loglf, theta, M, z, fit='composite'):
    # SED power law index is from Beta's paper.
    L = luminosity(M)
    if fit=='individual':
        # If this gammapi calculation is for an individual fit (in,
        # say, fitlf.py) then loglf might not have any z argument.
        return (10.0**loglf(theta, M))*L
    return (10.0**loglf(theta, M, z))*L


def emissivity_1450(loglf, theta, z, mlims, fit='composite'):
    # mlims = (lowest magnitude, brightest magnitude)
    #       = (brightest magnitude, faintest magnitude)
    m = np.linspace(mlims[0], mlims[1], num=1000)
    if fit=='individual':
        farr = f_1450(loglf, theta, m, z, fit='individual')
    else:
        farr = f_1450(loglf, theta, m, z)
    return np.trapz(farr, m) # erg s^-1 Hz^-1 Mpc^-3


def get_emissivity_1450(lfi, z, Mfaint=-18.0):

    rindices = np.random.randint(len(lfi.samples), size=300)
    e = np.array([emissivity_1450(lfi.log10phi, theta, z, (-30.0, Mfaint), fit='individual')
                          for theta
                          in lfi.samples[rindices]])
    l = np.percentile(e, 15.87) 
    u = np.percentile(e, 84.13)
    c = np.mean(e)
    lfi.emissivity_1450 = [u, l, c]

    return 



def Gamma_HI(loglf, theta, z, fit='composite'):

    if fit=='composite':
        fit_type = 'composite'
    else:
        fit_type = 'individual' 

    # Taken from Equation 11 of Lusso et al. 2015.
    em = emissivity(loglf, theta, z, (-30.0, -23.0), fit=fit_type)
    alpha_EUV = -1.7
    part1 = 4.6e-13 * (em/1.0e24) * ((1.0+z)/5.0)**(-2.4) / (1.5-alpha_EUV) # s^-1 

    em = emissivity(loglf, theta, z, (-23.0, -18.0), fit=fit_type)
    alpha_EUV = -0.56
    part2 = 4.6e-13 * (em/1.0e24) * ((1.0+z)/5.0)**(-2.4) / (1.5-alpha_EUV) # s^-1

    return part1+part2 


def Gamma_HI_singleslope(loglf, theta, z, fit='composite'):

    if fit=='composite':
        fit_type = 'composite'
    else:
        fit_type = 'individual' 

    # Taken from Equation 11 of Lusso et al. 2015.
    em = emissivity(loglf, theta, z, (-30.0, -18.0), fit=fit_type)
    alpha_EUV = -1.7
    return 4.6e-13 * (em/1.0e24) * ((1.0+z)/5.0)**(-2.4) / (1.5-alpha_EUV) # s^-1

def get_gamma_error(individuals):

    g_up = []
    g_low = []

    for x in individuals:

        z = x.z.mean()

        lowlim = np.percentile(x.samples, 15.87, axis=0)
        rate = rtg.gamma_HI(z, x.log10phi, lowlim, individual=True)
        rate = np.log10(rate)+12.0
        g_low.append(rate)

        uplim = np.percentile(x.samples, 84.13, axis=0)
        rate = rtg.gamma_HI(z, x.log10phi, uplim, individual=True)
        rate = np.log10(rate)+12.0
        g_up.append(rate)
        
    g_up = np.array(g_up)
    g_low = np.array(g_low)

    return g_up, g_low 
    

def plot_gamma(composite, individuals=None, zlims=(2.0,6.5), dirname='', fast=True, rt=False, lsa=False):

    """
    Calculates and plots HI photoionization rate. 

    rt   = True: uses the integral solution to the cosmological RT equation 
    lsa  = True: uses local source approximation 
    fast = True: reads stored values instead of calculating again 

    """

    zmin, zmax = zlims 
    z = np.linspace(zmin, zmax, num=10) 

    fig = plt.figure(figsize=(7, 7), dpi=100)
    ax = fig.add_subplot(1, 1, 1)

    ax.tick_params('both', which='major', length=7, width=1)
    ax.tick_params('both', which='minor', length=5, width=1)

    if lsa:

        rindices = np.random.randint(len(composite.samples), size=900)
        for theta in composite.samples[rindices]:
            g = np.array([Gamma_HI(composite.log10phi, theta, rs) for rs in z])
            g = np.log10(g)+12.0
            ax.plot(z, g, color='#67a9cf', alpha=0.1, zorder=1)

        bf = composite.samples.mean(axis=0)
        g = np.array([Gamma_HI(composite.log10phi, bf, rs) for rs in z])
        g = np.log10(g)+12.0
        ax.plot(z, g, color='k', zorder=2)

    if rt:
        
        if fast:
            data = np.load('gammapi.npz')
            z = data['z']
            ga = data['ga']
            g_mean = np.mean(ga, axis=0)
            g_up = np.percentile(ga, 15.87, axis=0)
            g_low = np.percentile(ga, 100.0-15.87, axis=0)
            ax.fill_between(z, g_low, g_up, color='#67a9cf', alpha=0.6, edgecolor='None', zorder=1) 
            ax.plot(z, g_mean, color='k', zorder=2)
        else:
            theta = composite.samples[np.random.randint(len(composite.samples))]
            ga = np.array([rtg.gamma_HI(rs, composite.log10phi, theta) for rs in z])
            ga = np.log10(ga)+12.0
            count = 1 
            print(count) 
            rindices = np.random.randint(len(composite.samples), size=100)
            for theta in composite.samples[rindices]:
                g = np.array([rtg.gamma_HI(rs, composite.log10phi, theta) for rs in z])
                count += 1
                print(count) 
                g = np.log10(g)+12.0
                ax.plot(z, g, color='#67a9cf', alpha=0.3, zorder=1)
                ga = np.vstack((ga, g))
                
            bf = composite.samples.mean(axis=0)
            g = np.array([Gamma_HI(composite.log10phi, bf, rs) for rs in z])
            g = np.log10(g)+12.0
            ax.plot(z, g, color='k', zorder=2)

            np.savez('gammapi', z=z, ga=ga, g=g)

    ax.set_ylabel(r'$\log_{10}(\Gamma_\mathrm{HI}/10^{-12} \mathrm{s}^{-1})$')
    ax.set_xlabel('$z$')
    ax.set_xlim(2.,6.5)
    ax.set_ylim(-2.,0.5)
    ax.set_xticks((2,3,4,5,6))
    
    zm, gm, gm_up, gm_low = np.loadtxt('Data/BeckerBolton.dat',unpack=True) 

    ax.scatter(zm, gm, c='#d7191c', edgecolor='None', label='Becker and Bolton 2013', s=32)
    ax.errorbar(zm, gm, ecolor='#d7191c', capsize=5,
                yerr=np.vstack((gm_up, abs(gm_low))),
                fmt='None', zorder=3, mfc='#d7191c', mec='#d7191c',
                mew=1, ms=5)

    zm, gm, gm_sigma = np.loadtxt('Data/calverley.dat',unpack=True) 
    gm += 12.0
    ax.scatter(zm, gm, c='#99cc66', edgecolor='None', label='Calverley et al.~2011', s=32) 
    ax.errorbar(zm, gm, ecolor='#99CC66', capsize=5,
                yerr=gm_sigma, fmt='None', zorder=4, mfc='#99CC66',
                mec='#99CC66', mew=1, ms=5)

    if lsa:
        
        if individuals is not None:
            c = np.array([x.gammapi[2]+12.0 for x in individuals])
            u = np.array([x.gammapi[0]+12.0 for x in individuals])
            l = np.array([x.gammapi[1]+12.0 for x in individuals])
            uyerr = u-c
            lyerr = c-l 

            zs = np.array([x.z.mean() for x in individuals])
            uz = np.array([x.z.max() for x in individuals])
            lz = np.array([x.z.min() for x in individuals])
            uzerr = uz-zs
            lzerr = zs-lz 

            ax.errorbar(zs, c, ecolor='#404040', capsize=0,
                        yerr=np.vstack((uyerr,lyerr)),
                        xerr=np.vstack((lzerr,uzerr)), fmt='o',
                        mfc='#ffffff', mec='#404040', zorder=3, mew=1,
                        ms=5, label='Individual Fits')

    if rt:

        if individuals is not None:

            if fast:

                data = np.load('gammapi_individuals.npz')
                zs = data['zs']
                g = data['g']
                uzerr = data['uzerr']
                lzerr = data['lzerr']
                uyerr = data['uyerr']
                lyerr = data['lyerr']

                uyerr[-1]=-0.1
                uyerr[-2]=-0.1


                lyerr[-1]=-0.1
                lyerr[-2]=-0.1
                
                ax.scatter(zs, g, s=32, c='#ffffff', edgecolor='#404040', zorder=3, label='Individual fits')
                ax.errorbar(zs, g, ecolor='#404040', capsize=0,
                            yerr=np.vstack((uyerr,lyerr)),
                            xerr=np.vstack((lzerr,uzerr)),
                            fmt='None',zorder=2)

            else:
                    
                zs = np.array([x.z.mean() for x in individuals])
                uz = np.array([x.z.max() for x in individuals])
                lz = np.array([x.z.min() for x in individuals])
                uzerr = uz-zs
                lzerr = zs-lz 
                print(zs)

                g = []
                for x in individuals:
                    z = x.z.mean()
                    bf = x.samples.mean(axis=0)
                    rate = rtg.gamma_HI(z, x.log10phi, bf, individual=True)
                    rate = np.log10(rate)+12.0
                    g.append(rate)

                g = np.array(g)
                ax.scatter(zs, g, s=32, c='#ffffff', edgecolor='#404040', zorder=3, label='Individual fits')

                g_up, g_low = get_gamma_error(individuals)
                uyerr = g_up-g
                lyerr = g-g_low
                ax.errorbar(zs, g, ecolor='#404040', capsize=0,
                            yerr=np.vstack((uyerr,lyerr)),
                            xerr=np.vstack((lzerr,uzerr)),
                            fmt='None',zorder=2)

                np.savez('gammapi_individuals', zs=zs, g=g, uzerr=uzerr, lzerr=lzerr, uyerr=uyerr, lyerr=lyerr)
        
    plt.legend(loc='lower left', fontsize=14, handlelength=1,
               frameon=False, framealpha=0.0, labelspacing=.1,
               handletextpad=0.1, borderpad=0.01, scatterpoints=1)
    
    plt.savefig('gammapi.pdf',bbox_inches='tight')
    #plt.close('all')

    return

def draw(individuals, composite=None):

    """
    Calculates and plots HI photoionization rate. 

    """

    fig = plt.figure(figsize=(7, 7), dpi=100)
    ax = fig.add_subplot(1, 1, 1)

    ax.tick_params('both', which='major', length=7, width=1)
    ax.tick_params('both', which='minor', length=5, width=1)

    ax.set_ylabel(r'$\Gamma_\mathrm{HI}~[10^{-12} \mathrm{s}^{-1}]$')
    ax.set_xlabel('$z$')
    ax.set_xlim(0.,7)

    ax.set_ylim(1.0e-2,10)
    ax.set_yscale('log')
    # ax.set_xticks((2,3,4,5,6))

    locs = (1.0e-2, 1.0e-1, 1.0, 10.0)
    labels = ('0.01', '0.1', '1', '10')
    plt.yticks(locs, labels)

    if composite is not None:
        zmin = 2.
        zmax = 6.5
        z = np.linspace(zmin, zmax, num=10) 
        theta = composite.samples[np.random.randint(len(composite.samples))]
        ga = np.array([rtg.gamma_HI(rs, composite.log10phi, theta) for rs in z])

        count = 1 
        print(count) 
        rindices = np.random.randint(len(composite.samples), size=100)
        for theta in composite.samples[rindices]:
            g = np.array([rtg.gamma_HI(rs, composite.log10phi, theta) for rs in z])
            count += 1
            print(count) 
            ax.plot(z, g, color='#67a9cf', alpha=0.3, zorder=1)

        bf = composite.samples.median(axis=0)
        g = np.array([Gamma_HI(composite.log10phi, bf, rs) for rs in z])
        ax.plot(z, g, color='k', zorder=2)
        
    zm, gm, gm_up, gm_low = np.loadtxt('Data/BeckerBolton.dat',unpack=True)
    
    gml = 10.0**gm
    gml_up = 10.0**(gm+gm_up)-10.0**gm
    gml_low = 10.0**gm - 10.0**(gm-np.abs(gm_low))

    ax.scatter(zm, gml, c='#d7191c', edgecolor='None', label='Becker and Bolton 2013', s=64)
    ax.errorbar(zm, gml, ecolor='#d7191c', capsize=5, elinewidth=1.5, capthick=1.5,
                yerr=np.vstack((gml_low, gml_up)),
                fmt='None', zorder=1, mfc='#d7191c', mec='#d7191c',
                mew=1, ms=5)

    zm, gm, gm_sigma = np.loadtxt('Data/calverley.dat',unpack=True) 
    gm += 12.0

    gml = 10.0**gm
    gml_up = 10.0**(gm+gm_sigma)-10.0**gm
    gml_low = 10.0**gm - 10.0**(gm-gm_sigma)
    
    ax.scatter(zm, gml, c='#99cc66', edgecolor='None', label='Calverley et al.~2011', s=64) 
    ax.errorbar(zm, gml, ecolor='#99CC66', capsize=5, elinewidth=1.5, capthick=1.5,
                yerr=np.vstack((gml_low, gml_up)), fmt='None', zorder=1, mfc='#99CC66',
                mec='#99CC66', mew=1, ms=5)

    c = np.array([x.gammapi[2]+12.0 for x in individuals])
    u = np.array([x.gammapi[0]+12.0 for x in individuals])
    l = np.array([x.gammapi[1]+12.0 for x in individuals])

    gml = 10.0**c
    gml_up = 10.0**u-10.0**c
    gml_low = 10.0**c - 10.0**l
    
    zs = np.array([x.z.mean() for x in individuals])
    uz = np.array([x.z.max() for x in individuals])
    lz = np.array([x.z.min() for x in individuals])


    uz = np.array([x.zlims[0] for x in individuals])
    lz = np.array([x.zlims[1] for x in individuals])
    
    uzerr = uz-zs
    lzerr = zs-lz 

    ax.scatter(zs, gml, c='#ffffff', edgecolor='k',
               label='Individual fits ($M<-18$, local source approximation)',
               s=44, zorder=4, linewidths=1.5) 
    ax.errorbar(zs, gml, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                yerr=np.vstack((gml_low,gml_up)),
                xerr=np.vstack((lzerr,uzerr)), 
                mfc='#ffffff', mec='#404040', zorder=3, mew=1,
                ms=5)

    plt.legend(loc='lower left', fontsize=14, handlelength=1,
               frameon=False, framealpha=0.0, labelspacing=.1,
               handletextpad=0.1, borderpad=0.01, scatterpoints=1)
    
    plt.savefig('gammapi.pdf',bbox_inches='tight')
    #plt.close('all')

    return

def emissivity_MH15(z):

    # Madau and Haardt 2015 Equation (1) 
    
    loge = 25.15*np.exp(-0.0026*z) - 1.5*np.exp(-1.3*z)

    return 10.0**loge # erg s^-1 Hz^-1 Mpc^-3

def emissivity_HM12(z):

    # Haardt and Madau 2012 Equation (37) 
    
    e = 10.0**24.6 * (1.0+z)**4.68 * np.exp(-0.28*z) / (np.exp(1.77*z)+26.3)

    return e # erg s^-1 Hz^-1 Mpc^-3

def emissivity_Manti17(z):

    # Manti et al. 2017 (MNRAS 466 1160) Equation (9) 

    loge = 23.59 + 0.55*z - 0.062*z**2 + 0.0047*z**3 - 0.0012*z**4
    
    return 10.0**loge # erg s^-1 Hz^-1 Mpc^-3

def pd13(ax, only18=False, only21=False, style=False):

    z, e912_21, e912_18 = np.loadtxt('Data_new/emissivity_pd13.dat', usecols=(1,4,5), unpack=True)

    if style:
            ax.plot(z, e912_18*1.0e24, lw=2, color='k', zorder=1, label='Palanque-Delabrouille et al.\ 2013')
            return 
        
    if only18:
            ax.plot(z, e912_18*1.0e24, lw=1.5, color='c', zorder=1, label='Palanque-Delabrouille et al.\ 2013', dashes=[7,2])
            return 

    if only21:
            ax.plot(z, e912_21*1.0e24, lw=1.5, color='c', zorder=1, label='Palanque-Delabrouille et al.\ 2013', dashes=[7,2])
            return 
        
    ax.plot(z, e912_18*1.0e24, lw=1.5, color='sandybrown', zorder=1, dashes=[7,2])
    ax.plot(z, e912_21*1.0e24, lw=1.5, color='sandybrown', zorder=1, label='Palanque-Delabrouille et al.\ 2013 ($M_\mathrm{1450}<-21$; dashed $<-18$)')
    
    return 

def pd16(ax, only18=False, only21=False, style=False):

    z, e912_21, e912_18 = np.loadtxt('Data_new/emissivity_pd16.dat', usecols=(1,4,5), unpack=True)

    if style:
        ax.plot(z, e912_18*1.0e24, lw=2, color='k', zorder=1, label='Palanque-Delabrouille et al.\ 2016')
        return
    
    if only18:
        ax.plot(z, e912_18*1.0e24, lw=1.5, color='c', zorder=1, label='Palanque-Delabrouille et al.\ 2016')
        return

    if only21:
        ax.plot(z, e912_21*1.0e24, lw=1.5, color='c', zorder=1, label='Palanque-Delabrouille et al.\ 2016')
        return
    
    ax.plot(z, e912_18*1.0e24, lw=1.5, color='yellowgreen', zorder=1, dashes=[7,2])
    ax.plot(z, e912_21*1.0e24, lw=1.5, color='yellowgreen', zorder=1, label='Palanque-Delabrouille et al.\ 2016 ($M_\mathrm{1450}<-21$; dashed $<-18$)')
    
    return 

def c17(ax, only18=False, only21=False):

    z, e912_21, e912_18 = np.loadtxt('Data_new/emissivity_c17.dat', usecols=(1,4,5), unpack=True)

    if only18:
        ax.plot(z, e912_18*1.0e24, lw=1.5, color='dodgerblue', zorder=1, label='Caditz 2017')
        return

    if only21:
        ax.plot(z, e912_21*1.0e24, lw=1.5, color='dodgerblue', zorder=1, label='Caditz 2017')
        return
    
    ax.plot(z, e912_18*1.0e24, lw=1.5, color='peru', zorder=1, dashes=[7,2])
    ax.plot(z, e912_21*1.0e24, lw=1.5, color='peru', zorder=1, label='Caditz 2017 ($M_\mathrm{1450}<-21$; dashed $<-18$)')
    
    return

def akiyama18(ax, only18=False, only21=False, style='k'):

    z = 3.9
    e18 = 2.4331e24 # erg s^-1 Hz^-1 Mpc^-3
    e21 = 2.3358e24 # erg s^-1 Hz^-1 Mpc^-3

    if style:
        ax.scatter(z, e18, c='dodgerblue', edgecolor='None',
                   s=36, zorder=9, linewidths=2, label='Akiyama et al.\ 2018')
        z_lerr = np.array([3.9-3.5])
        z_uerr = np.array([4.3-3.9])
        ax.errorbar(z, e18, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_lerr, z_uerr)),
                zorder=9, mew=1, linewidths=1.5)
        return
        

    if only18:
        ax.scatter(z, e18, c='dodgerblue', edgecolor='None',
                   s=36, zorder=9, linewidths=2, label='Akiyama et al.\ 2018', marker='^')
        z_lerr = np.array([3.9-3.5])
        z_uerr = np.array([4.3-3.9])
        ax.errorbar(z, e18, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_lerr, z_uerr)),
                zorder=9, mew=1, linewidths=1.5)
        return

    if only21:
        ax.scatter(z, e21, c='dodgerblue', edgecolor='None',
                   s=36, zorder=9, linewidths=2, label='Akiyama et al.\ 2018', marker='^')
        z_lerr = np.array([3.9-3.5])
        z_uerr = np.array([4.3-3.9])
        ax.errorbar(z, e21, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_lerr, z_uerr)),
                zorder=9, mew=1, linewidths=1.5)
        return
    
    # when showing both Mlim=-18 and -21, only need to show one
    # because the two cases give almost the same result 
    ax.scatter(z, e21, c='gold', edgecolor='None',
               s=64, zorder=9, linewidths=2, label='Akiyama et al.\ 2018 ($M_\mathrm{1450}<-21$)')

    z_lerr = np.array([3.9-3.5])
    z_uerr = np.array([4.3-3.9])
    ax.errorbar(z, e21, ecolor='gold', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_lerr, z_uerr)),
                zorder=9, mew=1, linewidths=1.5)
    
    return

def parsa18(ax, only18=False, only21=False, style=False):

    z = np.array([4.25, 4.75, 5.75])
    e18 = np.array([3.9619, 1.5898, 0.3401])*1.0e24
    e21 = np.array([2.6278, 1.0707, 0.2323])*1.0e24

    if style:
        ax.scatter(z, e18, c='k', edgecolor='None',
                   s=36, zorder=9, linewidths=2, label='Parsa et al.\ 2018')
        z_err = np.array([0.25, 0.25, 0.75])
        ax.errorbar(z, e18, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                    xerr=z_err,
                    zorder=9, mew=1, linewidths=1.5)

    if only18:
        ax.scatter(z, e18, c='dodgerblue', edgecolor='None',
                   s=36, zorder=9, linewidths=2, label='Parsa et al.\ 2018', marker='D')
        z_err = np.array([0.25, 0.25, 0.75])
        ax.errorbar(z, e18, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                    xerr=z_err,
                    zorder=9, mew=1, linewidths=1.5)
    if only21:
        ax.scatter(z, e21, c='dodgerblue', edgecolor='None',
                   s=36, zorder=9, linewidths=2, label='Parsa et al.\ 2018', marker='D')
        z_err = np.array([0.25, 0.25, 0.75])
        ax.errorbar(z, e21, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                    xerr=z_err,
                    zorder=9, mew=1, linewidths=1.5)

    return

def masters12(ax, only18=False, only21=False, style=False):

    z = np.array([3.2, 4.0])
    z_lerr = np.array([3.2-3.1, 4.0-3.5])
    z_uerr = np.array([3.5-3.2, 5.0-4.0])
    
    e18 = np.array([5.3431, 1.7853])*1.0e24
    e21 = np.array([4.3646, 1.5072])*1.0e24

    if style:
        ax.scatter(z, e18, c='k', edgecolor='None',
                   s=36, zorder=9, linewidths=2, label='Masters et al.\ 2012')
        z_err = np.array([0.25, 0.25])
        ax.errorbar(z, e18, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                    xerr=np.vstack((z_lerr, z_uerr)),
                    zorder=9, mew=1, linewidths=1.5)
    if only18:
        ax.scatter(z, e18, c='dodgerblue', edgecolor='None',
                   s=66, zorder=9, linewidths=2, label='Masters et al.\ 2012', marker='*')
        z_err = np.array([0.25, 0.25])
        ax.errorbar(z, e18, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                    xerr=np.vstack((z_lerr, z_uerr)),
                    zorder=9, mew=1, linewidths=1.5)
    if only21:
        ax.scatter(z, e21, c='dodgerblue', edgecolor='None',
                   s=66, zorder=9, linewidths=2, label='Masters et al.\ 2012', marker='*')
        z_err = np.array([0.25, 0.25])
        ax.errorbar(z, e21, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                    xerr=np.vstack((z_lerr, z_uerr)),
                    zorder=9, mew=1, linewidths=1.5)

    return 

def giallongo15(ax, only18=False, only21=False, style=False):

    z = np.array([4.249, 4.748, 5.754])
    zu = np.array([4.5, 5.0, 6.5])
    zl = np.array([4.0, 4.5, 5.0])

    z_lerr = z-zl
    z_uerr = zu-z
    
    e18 = np.array([8.6671, 7.8168, 3.2252])*1.0e24
    e21 = np.array([6.4266, 4.7801, 2.1852])*1.0e24
 
    # ax.errorbar(zg, eg, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
    #             xerr=np.vstack((zg_lerr, zg_uerr)),
    #             yerr=np.vstack((eg_lerr, eg_uerr)), 
    #             zorder=3, mew=1)

    # ax.scatter(zg, eg, c='dodgerblue', edgecolor='None',
    #            label='Giallongo et al.\ 2015', marker='s',
    #            s=36, zorder=4, linewidths=1.5)

    if style:
        ax.scatter(z, e18, c='k', edgecolor='None',
                   s=36, zorder=4, linewidths=1.5,
                   label='Giallongo et al.\ 2015')
        ax.errorbar(z, e18, ecolor='k', capsize=0,
                    fmt='None', elinewidth=1.5,
                    xerr=np.vstack((z_lerr, z_uerr)),
                    zorder=3, mew=1, linewidths=1.5)

    if only18:
        ax.scatter(z, e18, c='dodgerblue', edgecolor='None',
                   s=36, zorder=4, linewidths=1.5,
                   label='Giallongo et al.\ 2015', marker='s')
        ax.errorbar(z, e18, ecolor='dodgerblue', capsize=0,
                    fmt='None', elinewidth=1.5,
                    xerr=np.vstack((z_lerr, z_uerr)),
                    zorder=3, mew=1, linewidths=1.5)
    if only21:
        ax.scatter(z, e21, c='dodgerblue', edgecolor='None',
                   s=36, zorder=4, linewidths=1.5,
                   label='Giallongo et al.\ 2015', marker='s')
        ax.errorbar(z, e21, ecolor='dodgerblue', capsize=0,
                    fmt='None', elinewidth=1.5,
                    xerr=np.vstack((z_lerr, z_uerr)),
                    zorder=3, mew=1, linewidths=1.5)

    return 


def bongiorno07(ax, only18=False, only21=False, style=False):

    z, e912_21, e912_18 = np.loadtxt('Data_new/emissivity_b07.dat', usecols=(1,4,5), unpack=True)


    if style:
        ax.plot(z, e912_18*1.0e24, lw=2, color='k', zorder=1, label='Bongiorno et al.\ 2007')
        return
    
    if only18:
        ax.plot(z, e912_18*1.0e24, lw=1.5, color='peru', zorder=1, label='Bongiorno et al.\ 2007')
        return

    if only21:
        ax.plot(z, e912_21*1.0e24, lw=1.5, color='peru', zorder=1, label='Bongiorno et al.\ 2007')
        return
    
    return
    
        
def draw_emissivity(all_individuals, composite=None, select=False):

    """
    Calculates and plots LyC emissivity.

    """

    fig = plt.figure(figsize=(11.33, 7), dpi=100)
    ax = fig.add_subplot(1, 1, 1)
    plt.minorticks_on()
    ax.tick_params('both', which='major', length=7, width=1, zorder=20)
    ax.tick_params('both', which='minor', length=5, width=1, zorder=20)
    ax.set_ylabel(r'$\epsilon_{912}$ [erg s$^{-1}$ Hz$^{-1}$ cMpc$^{-3}$]')
    ax.set_xlabel('$z$')
    ax.set_xlim(-0.2,7.)
    ax.set_yscale('log')
    ax.set_ylim(4.0e22, 2.0e26)
    ax.set_axisbelow(False)
    
    # These redshift bins are labelled "bad" and are plotted differently.
    reject = [0, 1, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    
    m = np.ones(len(all_individuals), dtype=bool)
    m[reject] = False
    minv = np.logical_not(m) 
    individuals_good = [x for i, x in enumerate(all_individuals) if i not in set(reject)]

    # Plot individual emissivits for Mlim = -18 
    for x in individuals_good:
        get_emissivity(x, x.z.mean(), Mfaint=-18.0)
    c = np.array([x.emissivity[2] for x in individuals_good])
    u = np.array([x.emissivity[0] for x in individuals_good])
    l = np.array([x.emissivity[1] for x in individuals_good])
    em = c
    em_up = u - c
    em_low = c - l 
    zs = np.array([x.z.mean() for x in individuals_good])
    uz = np.array([x.zlims[0] for x in individuals_good])
    lz = np.array([x.zlims[1] for x in individuals_good])
    uzerr = uz-zs
    lzerr = zs-lz 
    ax.errorbar(zs, em, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                yerr=np.vstack((em_low, em_up)),
                xerr=np.vstack((lzerr, uzerr)), 
                mfc='#ffffff', mec='#404040', zorder=6, mew=1,
                ms=5)
    ax.scatter(zs, em, c='#ffffff', edgecolor='k',
               label='This work ($M_\mathrm{1450}<-18$)',
               s=48, zorder=6, linewidths=1.5)

    tabulate = True
    if tabulate:
        # This will ruin the fits below so turn off when not in use!
        # See emissivity.txt and tabulate_emissivity.py for how to use
        # this information.

        zs = np.array([x.z.mean() for x in all_individuals])
        uz = np.array([x.zlims[0] for x in all_individuals])
        lz = np.array([x.zlims[1] for x in all_individuals])
        uzerr = uz-zs
        lzerr = zs-lz 
        
        for x in all_individuals:
            get_emissivity(x, x.z.mean(), Mfaint=-18.0)
        c2 = np.array([x.emissivity[2] for x in all_individuals])
        u2 = np.array([x.emissivity[0] for x in all_individuals])
        l2 = np.array([x.emissivity[1] for x in all_individuals])
        em = c2
        em_up = u2 - c2
        em_low = c2 - l2 

        for x in all_individuals:
            get_emissivity_1450(x, x.z.mean(), Mfaint=-18.0)
        c2 = np.array([x.emissivity_1450[2] for x in all_individuals])
        u2 = np.array([x.emissivity_1450[0] for x in all_individuals])
        l2 = np.array([x.emissivity_1450[1] for x in all_individuals])
        em_1450 = c2
        em_up_1450 = u2 - c2
        em_low_1450 = c2 - l2

        for x in all_individuals:
            get_emissivity(x, x.z.mean(), Mfaint=-21.0)
        c2 = np.array([x.emissivity[2] for x in all_individuals])
        u2 = np.array([x.emissivity[0] for x in all_individuals])
        l2 = np.array([x.emissivity[1] for x in all_individuals])
        em21 = c2
        em21_up = u2 - c2
        em21_low = c2 - l2 

        for x in all_individuals:
            get_emissivity_1450(x, x.z.mean(), Mfaint=-21.0)
        c2 = np.array([x.emissivity_1450[2] for x in all_individuals])
        u2 = np.array([x.emissivity_1450[0] for x in all_individuals])
        l2 = np.array([x.emissivity_1450[1] for x in all_individuals])
        em21_1450 = c2
        em21_up_1450 = u2 - c2
        em21_low_1450 = c2 - l2 
        
        for i in range(len(zs)):
            print((zs[i], lz[i], uz[i], em[i]/1.0e24, em_up[i]/1.0e24, em_low[i]/1.0e24, em_1450[i]/1.0e24, em_up_1450[i]/1.0e24, em_low_1450[i]/1.0e24, em21[i]/1.0e24, em21_up[i]/1.0e24, em21_low[i]/1.0e24, em21_1450[i]/1.0e24, em21_up_1450[i]/1.0e24, em21_low_1450[i]/1.0e24))

        return 
            
    # Plot best-fit model for Mlim=-18
    def func(z, a, b, c, d, e):
        e = 10.0**a * (1.0+z)**b * np.exp(-c*z) / (np.exp(d*z)+e)
        return e # erg s^-1 Hz^-1 Mpc^-3

    sigma = u-l 
    z = np.linspace(0.0, 7, num=1000)
    samples = fit_emissivity.fit(zs, em, sigma)
    nsample = 300
    rsample = samples[np.random.randint(len(samples), size=nsample)]
    nzs = len(z) 
    e = np.zeros((nsample, nzs))
    for i, theta in enumerate(rsample):
        e[i] = np.array(func(z, *theta))

    up = np.percentile(e, 15.87, axis=0)
    down = np.percentile(e, 84.13, axis=0)
    tw18f = ax.fill_between(z, down, y2=up, color='red', zorder=5, alpha=0.6, edgecolor='None')
    b = np.median(e, axis=0)
    tw18, = plt.plot(z, b, lw=2, c='red', zorder=5)

    # Plot individual emissivits for Mlim = -21
    for x in individuals_good:
        get_emissivity(x, x.z.mean(), Mfaint=-21.0)
    c = np.array([x.emissivity[2] for x in individuals_good])
    u = np.array([x.emissivity[0] for x in individuals_good])
    l = np.array([x.emissivity[1] for x in individuals_good])
    em = c
    em_up = u - c
    em_low = c - l 
    zs = np.array([x.z.mean() for x in individuals_good])
    uz = np.array([x.zlims[0] for x in individuals_good])
    lz = np.array([x.zlims[1] for x in individuals_good])
    uzerr = uz-zs
    lzerr = zs-lz 
    ax.scatter(zs, em, c='k', edgecolor='k',
               label='This work ($M_\mathrm{1450}<-21$)',
               s=48, zorder=11, linewidths=1.5) 
    ax.errorbar(zs, em, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                yerr=np.vstack((em_low, em_up)),
                xerr=np.vstack((lzerr, uzerr)), 
                mfc='#ffffff', mec='#404040', zorder=11, mew=1,
                ms=5)

    for x in individuals_good:
        get_emissivity_1450(x, x.z.mean(), Mfaint=-21.0)
    c2 = np.array([x.emissivity_1450[2] for x in individuals_good])
    u2 = np.array([x.emissivity_1450[0] for x in individuals_good])
    l2 = np.array([x.emissivity_1450[1] for x in individuals_good])
    em_1450 = c2
    em_up_1450 = u2 - c2
    em_low_1450 = c2 - l2 
    
    if tabulate:

        zs = np.array([x.z.mean() for x in all_individuals])
        uz = np.array([x.zlims[0] for x in all_individuals])
        lz = np.array([x.zlims[1] for x in all_individuals])
        uzerr = uz-zs
        lzerr = zs-lz 
        
        for x in all_individuals:
            get_emissivity(x, x.z.mean(), Mfaint=-21.0)
        c2 = np.array([x.emissivity[2] for x in all_individuals])
        u2 = np.array([x.emissivity[0] for x in all_individuals])
        l2 = np.array([x.emissivity[1] for x in all_individuals])
        em = c2
        em_up = u2 - c2
        em_low = c2 - l2 

        for x in all_individuals:
            get_emissivity_1450(x, x.z.mean(), Mfaint=-21.0)
        c2 = np.array([x.emissivity_1450[2] for x in all_individuals])
        u2 = np.array([x.emissivity_1450[0] for x in all_individuals])
        l2 = np.array([x.emissivity_1450[1] for x in all_individuals])
        em_1450 = c2
        em_up_1450 = u2 - c2
        em_low_1450 = c2 - l2 
        
        for i in range(len(zs)):
            print((zs[i], lz[i], uz[i], em[i]/1.0e23, em_up[i]/1.0e23, em_low[i]/1.0e23, em_1450[i]/1.0e23, em_up_1450[i]/1.0e23, em_low_1450[i]/1.0e23))    

    sigma = u-l 
    samples = fit_emissivity.fit(zs, em, sigma)
    nsample = 300
    rsample = samples[np.random.randint(len(samples), size=nsample)]
    nzs = len(z) 
    e = np.zeros((nsample, nzs))
    for i, theta in enumerate(rsample):
        e[i] = np.array(func(z, *theta))
    up = np.percentile(e, 15.87, axis=0)
    down = np.percentile(e, 84.13, axis=0)
    tw21f = ax.fill_between(z, down, y2=up, color='blue', zorder=7, alpha=0.6, edgecolor='None')
    b = np.median(e, axis=0)
    tw21, = plt.plot(z, b, lw=2, c='blue', zorder=7)
    
    tabulate = False
    if tabulate:
        for i in range(len(em21)):
            print((r'{:.1f}  {:.3e}  {:.3e}'.format(z[i], em18[i], em21[i])))
            
    zg, eg, zg_lerr, zg_uerr, eg_lerr, eg_uerr = np.loadtxt('Data_new/giallongo15_emissivity.txt', unpack=True)
    
    eg *= 1.0e24
    eg_lerr *= 1.0e24
    eg_uerr *= 1.0e24
    ax.errorbar(zg, eg, ecolor='tomato', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((zg_lerr, zg_uerr)),
                yerr=np.vstack((eg_lerr, eg_uerr)), 
                zorder=3, mew=1)

    ax.scatter(zg, eg, c='#ffffff', edgecolor='tomato',
               label='Giallongo et al.\ 2015 ($M_\mathrm{1450}<-18$)',
               s=60, zorder=4, linewidths=1.5)

    e_MH15 = emissivity_MH15(z)
    # ax.plot(z, e_MH15, lw=2, c='forestgreen', label='Madau and Haardt 2015', zorder=1)
    ax.plot(z, e_MH15, lw=1, c='darkgreen', label='Madau and Haardt 2015', zorder=1, dashes=[1,1])

    e_HM12 = emissivity_HM12(z)
    ax.plot(z, e_HM12, lw=2, c='brown', label='Haardt and Madau 2012', zorder=3, dashes=[7,2])

    e_M17 = emissivity_Manti17(z)
    ax.plot(z, e_M17, lw=2, c='grey', label='Manti et al.\ 2017 ($M_\mathrm{1450}<-19$)', zorder=2, dashes=[7,2])

    # Emissivity at z = 0 from Schulze et al. 2009 A&A 507 781.  This
    # number is rederived by Gabor.  See his email of 8 March 2018.
    z_Schulze09 = np.array([0.0])
    e_Schulze09 = np.array([0.2561e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_Schulze09, e_Schulze09, c='#ffffff', edgecolor='peru',
               s=60, zorder=12, linewidths=2)

    z_Schulze09 = np.array([0.0])
    e_Schulze09 = np.array([0.0435e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_Schulze09, e_Schulze09, c='peru', edgecolor='None',
               label='Schulze et al.\ 2009 ($M_\mathrm{1450}<-21$; open circle $<-18$)', s=64, zorder=9)
    
    # Emissivity at z = 5 from McGreer et al. 2018 AJ 155 131.  This
    # number is rederived by Gabor.  See his email of 12 March 2018.
    z_McGreer18 = np.array([4.9])
    e_McGreer18 = np.array([0.9641e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_McGreer18, e_McGreer18, c='None', edgecolor='limegreen',
               s=60, zorder=10, linewidths=2)

    z_McGreer_lerr = np.array([4.9-4.7])
    z_McGreer_uerr = np.array([5.1-4.9])
    ax.errorbar(z_McGreer18, e_McGreer18, ecolor='limegreen', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_McGreer_lerr, z_McGreer_uerr)),
                zorder=10, mew=1, linewidths=1.5)
    

    z_McGreer18 = np.array([4.9])
    e_McGreer18 = np.array([0.6836e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_McGreer18, e_McGreer18, c='limegreen', edgecolor='None',
               label='McGreer et al.\ 2018 ($M_\mathrm{1450}<-21$; open circle $<-18$)', s=64, zorder=10)

    ax.errorbar(z_McGreer18, e_McGreer18, ecolor='limegreen', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_McGreer_lerr, z_McGreer_uerr)),
                zorder=10, mew=1, linewidths=1.5)
    
    # Emissivity at z = 5 from McGreer et al. 2018 AJ 155 131.  This
    # number is rederived by Gabor.  See his email of 12 March 2018.

    zmin_Onoue17 = 5.5
    emin_Onoue17 = 0.1531e24
    zmax_Onoue17 = 6.5
    emax_Onoue17 = 0.2051e24
    dz_Onoue17 = zmax_Onoue17 - zmin_Onoue17
    de_Onoue17 = emax_Onoue17 - emin_Onoue17
    rect = mpatches.Rectangle((zmin_Onoue17, emin_Onoue17),  dz_Onoue17, de_Onoue17, ec='orange', color='None', lw=2, zorder=10)
    ax.add_patch(rect)

    emin_Onoue17 = 0.1118e24
    emax_Onoue17 = 0.1299e24
    de_Onoue17 = emax_Onoue17 - emin_Onoue17
    rect = mpatches.Rectangle((zmin_Onoue17, emin_Onoue17),  dz_Onoue17, de_Onoue17, ec='None', color='orange', zorder=10, label='Onoue et al.\ 2017 ($M_\mathrm{1450}<-21$; open $<-18$)')
    ax.add_patch(rect)
    
    
    z_Onoue17 = np.array([6.0])
    e_Onoue17 = np.array([0.1531e24]) # erg/s/Hz/Mpc^3
    # ax.scatter(z_Onoue17, e_Onoue17, c='None', edgecolor='b',
    #            s=60, zorder=9, linewidths=2)

    z_Onoue17 = np.array([6.0])
    e_Onoue17 = np.array([0.1118e24]) # erg/s/Hz/Mpc^3
    # ax.scatter(z_Onoue17, e_Onoue17, c='b', edgecolor='None',
    #            label='Onoue et al.\ 2017 ($M_\mathrm{1450}<-18$; open circle $<-18$)', s=64, zorder=9)

    z_Onoue17 = np.array([6.0])
    e_Onoue17 = np.array([0.2051e24]) # erg/s/Hz/Mpc^3
    # ax.scatter(z_Onoue17, e_Onoue17, c='None', edgecolor='b',
    #            s=60, zorder=9, linewidths=2, marker='^')

    z_Onoue17 = np.array([6.0])
    e_Onoue17 = np.array([0.1299e24]) # erg/s/Hz/Mpc^3
    # ax.scatter(z_Onoue17, e_Onoue17, c='b', edgecolor='None',
    #            label='Onoue et al.\ 2017 (including Parsa et al.\ 2017 source)', s=64, zorder=9, marker='^')
    
    pd13(ax)

    pd16(ax)

    c17(ax)

    akiyama18(ax)
    
    if composite is not None:
        zc = np.linspace(0, 7, 200)
        bf = np.median(composite.samples, axis=0)

        nsample = 300
        rsample = composite.samples[np.random.randint(len(composite.samples), size=nsample)]
        nzs = len(zc) 
        e = np.zeros((nsample, nzs))

        for i, theta in enumerate(rsample):
            e[i] = np.array([emissivity(composite.log10phi, theta, x, (-30.0, -18.0)) for x in zc])

        up = np.percentile(e, 15.87, axis=0)
        down = np.percentile(e, 84.13, axis=0)
        ax.fill_between(zc, down, y2=up, color='goldenrod', zorder=1)

        e = np.array([emissivity(composite.log10phi, bf, x, (-30.0, -18.0)) for x in zc])
        ax.plot(zc, e, c='k', lw=2) 


    handles, labels = ax.get_legend_handles_labels()
    handles.append((tw18f,tw18))
    labels.append('This work; fit ($M_\mathrm{1450}<-18$)')
    handles.append((tw21f,tw21))
    labels.append('This work; fit ($M_\mathrm{1450}<-21$)')
    myorder = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 7, 8, 13, 14]
    handles = [handles[x] for x in myorder]
    labels = [labels[x] for x in myorder]

    plt.legend(handles, labels, loc='upper right', fontsize=10, handlelength=3,
               frameon=False, framealpha=0.0, labelspacing=.1, ncol=2,
               handletextpad=0.1, borderpad=0.01, scatterpoints=1, borderaxespad=1)

    
    plt.savefig('emissivity.pdf',bbox_inches='tight')
    #plt.close('all')

    return


def get_gammapi_percentiles(lfi, z):

    """
    Calculate photoionization rate posterior mean value and 1-sigma
    percentile.

    """
    rindices = np.random.randint(len(lfi.samples), size=300)
    g = np.array([np.log10(Gamma_HI(lfi.log10phi, theta, z,
                                            fit='individual'))
                  for theta
                  in lfi.samples[rindices]])
    u = np.percentile(g, 15.87) 
    l = np.percentile(g, 84.13)
    c = np.mean(g)
    lfi.gammapi = [u, l, c]

    return 


def draw_emissivity_18(all_individuals, composite=None, select=False):

    """
    Calculates and plots LyC emissivity.

    """

    fig = plt.figure(figsize=(7, 7), dpi=100)
    ax = fig.add_subplot(1, 1, 1)
    plt.minorticks_on()
    ax.tick_params('both', which='major', length=7, width=1, zorder=20)
    ax.tick_params('both', which='minor', length=5, width=1, zorder=20)
    ax.set_ylabel(r'$\epsilon_{912}$ [erg s$^{-1}$ Hz$^{-1}$ cMpc$^{-3}$]')
    ax.set_xlabel('$z$')
    ax.set_xlim(-0.2,7.)
    ax.set_yscale('log')
    ax.set_ylim(4.0e22, 2.0e25)
    ax.set_axisbelow(False)
    
    # These redshift bins are labelled "bad" and are plotted differently.
    reject = [0, 1, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    
    m = np.ones(len(all_individuals), dtype=bool)
    m[reject] = False
    minv = np.logical_not(m) 
    individuals_good = [x for i, x in enumerate(all_individuals) if i not in set(reject)]
    individuals_bad = [x for i, x in enumerate(all_individuals) if i in set(reject)]

    # Plot individual emissivits for Mlim = -18 
    for x in individuals_good:
        get_emissivity(x, x.z.mean(), Mfaint=-18.0)
    c = np.array([x.emissivity[2] for x in individuals_good])
    u = np.array([x.emissivity[0] for x in individuals_good])
    l = np.array([x.emissivity[1] for x in individuals_good])
    em = c
    em_up = u - c
    em_low = c - l 
    zs = np.array([x.z.mean() for x in individuals_good])
    uz = np.array([x.zlims[0] for x in individuals_good])
    lz = np.array([x.zlims[1] for x in individuals_good])
    uzerr = uz-zs
    lzerr = zs-lz 
    ax.errorbar(zs, em, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                yerr=np.vstack((em_low, em_up)),
                xerr=np.vstack((lzerr, uzerr)), 
                mfc='#ffffff', mec='#404040', zorder=6, mew=1,
                ms=5)
    ax.scatter(zs, em, c='k', edgecolor='None',
               label='Kulkarni et al.\ 2019 (this work)',
               s=36, zorder=6, linewidths=1.5) 

    # npz produced using rhoqso_fit.get_fit_mcmc(). 
    data = np.load('e1450_18_21feb.npz')
    z = data['z']
    b = data['median']*((912.0/1450.0)**0.61)
    up = data['up']*((912.0/1450.0)**0.61)
    down = data['down']*((912.0/1450.0)**0.61)
    tw18f = ax.fill_between(z, down, y2=up, color='red', zorder=5, alpha=0.6, edgecolor='None')
    tw18, = plt.plot(z, b, lw=2, c='red', zorder=5)
    
    show_bad = True
    if show_bad:
        for x in individuals_bad:
            get_emissivity(x, x.z.mean(), Mfaint=-18.0)
        c = np.array([x.emissivity[2] for x in individuals_bad])
        u = np.array([x.emissivity[0] for x in individuals_bad])
        l = np.array([x.emissivity[1] for x in individuals_bad])
        em = c
        em_up = u - c
        em_low = c - l 
        zs = np.array([x.z.mean() for x in individuals_bad])
        uz = np.array([x.zlims[0] for x in individuals_bad])
        lz = np.array([x.zlims[1] for x in individuals_bad])
        uzerr = uz-zs
        lzerr = zs-lz 
        ax.errorbar(zs, em, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                    yerr=np.vstack((em_low, em_up)),
                    xerr=np.vstack((lzerr, uzerr)), 
                    mfc='#ffffff', mec='#404040', zorder=6, mew=1,
                    ms=5)
        ax.scatter(zs, em, c='#ffffff', edgecolor='k',
                   s=42, zorder=6, linewidths=1.5) 

    giallongo15(ax, only18=True)
    
    e_MH15 = emissivity_MH15(z)
    ax.plot(z, e_MH15, lw=1, c='darkgreen', label='Madau and Haardt 2015', zorder=1, dashes=[1,1])

    e_HM12 = emissivity_HM12(z)
    ax.plot(z, e_HM12, lw=2, c='brown', label='Haardt and Madau 2012', zorder=3, dashes=[7,2])

    e_M17 = emissivity_Manti17(z)
    ax.plot(z, e_M17, lw=2, c='grey', label='Manti et al.\ 2017', zorder=2, dashes=[7,2])

    # Emissivity at z = 0 from Schulze et al. 2009 A&A 507 781.  This
    # number is rederived by Gabor.  See his email of 8 March 2018.
    z_Schulze09 = np.array([0.0])
    e_Schulze09 = np.array([0.2561e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_Schulze09, e_Schulze09, c='dodgerblue', edgecolor='None', marker='p',
               s=36, zorder=12, linewidths=2, label='Schulze et al.\ 2009')

    # Emissivity at z = 5 from McGreer et al. 2018 AJ 155 131.  This
    # number is rederived by Gabor.  See his email of 12 March 2018.
    z_McGreer18 = np.array([4.9])
    e_McGreer18 = np.array([0.9641e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_McGreer18, e_McGreer18, c='dodgerblue', edgecolor='None',
               s=36, zorder=10, linewidths=2, label='McGreer et al.\ 2018')

    z_McGreer_lerr = np.array([4.9-4.7])
    z_McGreer_uerr = np.array([5.1-4.9])
    ax.errorbar(z_McGreer18, e_McGreer18, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_McGreer_lerr, z_McGreer_uerr)),
                zorder=10, mew=1, linewidths=1.5)
    
    zmin_Onoue17 = 5.5
    emin_Onoue17 = 0.1531e24
    zmax_Onoue17 = 6.5
    emax_Onoue17 = 0.2051e24
    dz_Onoue17 = zmax_Onoue17 - zmin_Onoue17
    de_Onoue17 = emax_Onoue17 - emin_Onoue17
    rect = mpatches.Rectangle((zmin_Onoue17, emin_Onoue17),
                              dz_Onoue17, de_Onoue17,
                              ec='dodgerblue', color='None',
                              lw=2, zorder=10, label='Onoue et al.\ 2017')
    ax.add_patch(rect)

    pd13(ax, only18=True)

    pd16(ax, only18=True)

    c17(ax, only18=True)

    akiyama18(ax, only18=True)

    parsa18(ax, only18=True)

    masters12(ax, only18=True)

    handles, labels = ax.get_legend_handles_labels()
    handles.append((tw18f,tw18))
    labels.append('Kulkarni et al.\ 2019 (this work; fit)')

    print((len(handles)))
    for i, x in enumerate(labels):
        print((i, x)) 

    myorder = [9, 13, 8, 11, 10, 12, 6, 0, 1, 2, 3, 4, 5, 7, 14]
    handles = [handles[x] for x in myorder]
    labels = [labels[x] for x in myorder]
    
    plt.legend(handles, labels, loc='center', fontsize=12, handlelength=3,
               frameon=False, framealpha=0.0, labelspacing=.1, #ncol=2, columnspacing=2,
               handletextpad=0.1, borderpad=0.01, scatterpoints=1, borderaxespad=1, bbox_to_anchor=[0.4,0.25])

    plt.text(0.94, 0.94, '$M_\mathrm{1450}<-18$', horizontalalignment='right',
             verticalalignment='center', transform=ax.transAxes, fontsize='16')
    
    
    plt.savefig('emissivity_18.pdf',bbox_inches='tight')
    #plt.close('all')

    return


def draw_emissivity_18_talk(all_individuals, zlims, composite=None, select=False):

    """
    Calculates and plots LyC emissivity.

    """

    fig = plt.figure(figsize=(7, 7), dpi=100)
    ax = fig.add_subplot(1, 1, 1)
    plt.minorticks_on()
    ax.tick_params('both', which='major', length=7, width=1, zorder=20)
    ax.tick_params('both', which='minor', length=5, width=1, zorder=20)
    ax.set_ylabel(r'$\epsilon_{912}$ [erg s$^{-1}$ Hz$^{-1}$ cMpc$^{-3}$]')
    ax.set_xlabel('$z$')
    ax.set_xlim(-0.2,7.)
    ax.set_yscale('log')
    ax.set_ylim(4.0e22, 2.0e25)
    ax.set_axisbelow(False)
    
    # These redshift bins are labelled "bad" and are plotted differently.
    reject = [0, 1, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    
    m = np.ones(len(all_individuals), dtype=bool)
    m[reject] = False
    minv = np.logical_not(m) 
    individuals_good = [x for i, x in enumerate(all_individuals) if i not in set(reject)]
    individuals_bad = [x for i, x in enumerate(all_individuals) if i in set(reject)]

    # Plot individual emissivits for Mlim = -18 
    for x in individuals_good:
        get_emissivity(x, x.z.mean(), Mfaint=-18.0)
    c = np.array([x.emissivity[2] for x in individuals_good])
    u = np.array([x.emissivity[0] for x in individuals_good])
    l = np.array([x.emissivity[1] for x in individuals_good])
    em = c
    em_up = u - c
    em_low = c - l 
    zs = np.array([x.z.mean() for x in individuals_good])
    uz = np.array([x.zlims[0] for x in individuals_good])
    lz = np.array([x.zlims[1] for x in individuals_good])
    uzerr = uz-zs
    lzerr = zs-lz 
    ax.errorbar(zs, em, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                yerr=np.vstack((em_low, em_up)),
                xerr=np.vstack((lzerr, uzerr)), 
                mfc='#ffffff', mec='#404040', zorder=20, mew=1,
                ms=5)
    ax.scatter(zs, em, c='k', edgecolor='None',
               label='Kulkarni et al.\ 2018 ($M_{1450}<-18$)',
               s=36, zorder=20, linewidths=1.5) 

    # Plot best-fit model for Mlim=-18
    def func(z, a, b, c, d, e):
        e = 10.0**a * (1.0+z)**b * np.exp(-c*z) / (np.exp(d*z)+e)
        return e # erg s^-1 Hz^-1 Mpc^-3

    sigma = u-l 
    z = np.linspace(0.0, 7, num=1000)
    samples = fit_emissivity.fit(zs, em, sigma)
    nsample = 300
    rsample = samples[np.random.randint(len(samples), size=nsample)]
    nzs = len(z) 
    e = np.zeros((nsample, nzs))
    for i, theta in enumerate(rsample):
        e[i] = np.array(func(z, *theta))

    up = np.percentile(e, 15.87, axis=0)
    down = np.percentile(e, 84.13, axis=0)
    tw18f = ax.fill_between(z, down, y2=up, color='red', zorder=5, alpha=0.6, edgecolor='None')
    b = np.median(e, axis=0)
    tw18, = plt.plot(z, b, lw=2, c='red', zorder=5)

    show_bad = False
    if show_bad:
        for x in individuals_bad:
            get_emissivity(x, x.z.mean(), Mfaint=-18.0)
        c = np.array([x.emissivity[2] for x in individuals_bad])
        u = np.array([x.emissivity[0] for x in individuals_bad])
        l = np.array([x.emissivity[1] for x in individuals_bad])
        em = c
        em_up = u - c
        em_low = c - l 
        zs = np.array([x.z.mean() for x in individuals_bad])
        uz = np.array([x.zlims[0] for x in individuals_bad])
        lz = np.array([x.zlims[1] for x in individuals_bad])
        uzerr = uz-zs
        lzerr = zs-lz 
        ax.errorbar(zs, em, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                    yerr=np.vstack((em_low, em_up)),
                    xerr=np.vstack((lzerr, uzerr)), 
                    mfc='#ffffff', mec='#404040', zorder=6, mew=1,
                    ms=5)
        ax.scatter(zs, em, c='#ffffff', edgecolor='k',
                   s=42, zorder=6, linewidths=1.5) 

    giallongo15(ax, only18=True)
    
    e_MH15 = emissivity_MH15(z)
    #ax.plot(z, e_MH15, lw=1, c='darkgreen', label='Madau and Haardt 2015', zorder=1, dashes=[1,1])

    e_HM12 = emissivity_HM12(z)
    ax.plot(z, e_HM12, lw=2, c='green', label='Haardt and Madau 2012', zorder=3)

    # e_M17 = emissivity_Manti17(z)
    # ax.plot(z, e_M17, lw=2, c='grey', label='Manti et al.\ 2017', zorder=2, dashes=[7,2])

    # Emissivity at z = 0 from Schulze et al. 2009 A&A 507 781.  This
    # number is rederived by Gabor.  See his email of 8 March 2018.
    z_Schulze09 = np.array([0.0])
    e_Schulze09 = np.array([0.2561e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_Schulze09, e_Schulze09, c='dodgerblue', edgecolor='None', marker='p',
               s=36, zorder=12, linewidths=2, label='Schulze et al.\ 2009')

    # Emissivity at z = 5 from McGreer et al. 2018 AJ 155 131.  This
    # number is rederived by Gabor.  See his email of 12 March 2018.
    z_McGreer18 = np.array([4.9])
    e_McGreer18 = np.array([0.9641e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_McGreer18, e_McGreer18, c='dodgerblue', edgecolor='None',
               s=36, zorder=10, linewidths=2, label='McGreer et al.\ 2018')

    z_McGreer_lerr = np.array([4.9-4.7])
    z_McGreer_uerr = np.array([5.1-4.9])
    ax.errorbar(z_McGreer18, e_McGreer18, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_McGreer_lerr, z_McGreer_uerr)),
                zorder=10, mew=1, linewidths=1.5)
    
    zmin_Onoue17 = 5.5
    emin_Onoue17 = 0.1531e24
    zmax_Onoue17 = 6.5
    emax_Onoue17 = 0.2051e24
    dz_Onoue17 = zmax_Onoue17 - zmin_Onoue17
    de_Onoue17 = emax_Onoue17 - emin_Onoue17
    rect = mpatches.Rectangle((zmin_Onoue17, emin_Onoue17),
                              dz_Onoue17, de_Onoue17,
                              ec='dodgerblue', color='None',
                              lw=2, zorder=10, label='Onoue et al.\ 2017')
    ax.add_patch(rect)

    #pd13(ax, only18=True)

    #pd16(ax, only18=True)

    #c17(ax, only18=True)

    #akiyama18(ax, only18=True)

    parsa18(ax, only18=True)

    masters12(ax, only18=True)

    #bongiorno07(ax, only18=True)
    
    handles, labels = ax.get_legend_handles_labels()
    handles.append((tw18f,tw18))
    labels.append('Kulkarni et al.\ 2018 (fit)')

    print((len(handles)))
    for i, x in enumerate(labels):
        print((i, x)) 

    myorder = [0,3,4,5,6,7,1,2,8]
    handles = [handles[x] for x in myorder]
    labels = [labels[x] for x in myorder]
    
    plt.legend(handles, labels, loc='center', fontsize=12, handlelength=3,
               frameon=False, framealpha=0.0, labelspacing=.1, #ncol=2, columnspacing=2,
               handletextpad=0.1, borderpad=0.01, scatterpoints=1, borderaxespad=1, bbox_to_anchor=[0.4,0.16])

    # plt.text(0.94, 0.94, '$M_\mathrm{1450}<-18$', horizontalalignment='right',
    #          verticalalignment='center', transform=ax.transAxes, fontsize='16')
    
    
    plt.savefig('emissivity_18_gabor_talk.pdf',bbox_inches='tight')
    #plt.close('all')

    return


def draw_emissivity_21(all_individuals, composite=None, select=False):

    """
    Calculates and plots LyC emissivity.

    """

    fig = plt.figure(figsize=(7, 7), dpi=100)
    ax = fig.add_subplot(1, 1, 1)
    plt.minorticks_on()
    ax.tick_params('both', which='major', length=7, width=1, zorder=20)
    ax.tick_params('both', which='minor', length=5, width=1, zorder=20)
    ax.set_ylabel(r'$\epsilon_{912}$ [erg s$^{-1}$ Hz$^{-1}$ cMpc$^{-3}$]')
    ax.set_xlabel('$z$')
    ax.set_xlim(-0.2,7.)
    ax.set_yscale('log')
    ax.set_ylim(4.0e22, 2.0e25)
    ax.set_axisbelow(False)
    
    # These redshift bins are labelled "bad" and are plotted differently.
    reject = [0, 1, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    
    m = np.ones(len(all_individuals), dtype=bool)
    m[reject] = False
    minv = np.logical_not(m) 
    individuals_good = [x for i, x in enumerate(all_individuals) if i not in set(reject)]
    individuals_bad = [x for i, x in enumerate(all_individuals) if i in set(reject)]

    # Plot individual emissivits for Mlim = -18 
    for x in individuals_good:
        get_emissivity(x, x.z.mean(), Mfaint=-21.0)
    c = np.array([x.emissivity[2] for x in individuals_good])
    u = np.array([x.emissivity[0] for x in individuals_good])
    l = np.array([x.emissivity[1] for x in individuals_good])
    em = c
    em_up = u - c
    em_low = c - l 
    zs = np.array([x.z.mean() for x in individuals_good])
    uz = np.array([x.zlims[0] for x in individuals_good])
    lz = np.array([x.zlims[1] for x in individuals_good])
    uzerr = uz-zs
    lzerr = zs-lz 
    ax.errorbar(zs, em, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                yerr=np.vstack((em_low, em_up)),
                xerr=np.vstack((lzerr, uzerr)), 
                mfc='#ffffff', mec='#404040', zorder=6, mew=1,
                ms=5)
    ax.scatter(zs, em, c='k', edgecolor='None',
               label='Kulkarni et al.\ 2019 (this work)',
               s=42, zorder=6, linewidths=1.5) 

    # npz produced using rhoqso_fit.get_fit_mcmc().
    data = np.load('e1450_21_21feb.npz')
    z = data['z']
    b = data['median']*((912.0/1450.0)**0.61)
    up = data['up']*((912.0/1450.0)**0.61)
    down = data['down']*((912.0/1450.0)**0.61)
    tw18f = ax.fill_between(z, down, y2=up, color='red', zorder=5, alpha=0.6, edgecolor='None')
    tw18, = plt.plot(z, b, lw=2, c='red', zorder=5)
    
    show_bad = True
    if show_bad:
        for x in individuals_bad:
            get_emissivity(x, x.z.mean(), Mfaint=-21.0)
        c = np.array([x.emissivity[2] for x in individuals_bad])
        u = np.array([x.emissivity[0] for x in individuals_bad])
        l = np.array([x.emissivity[1] for x in individuals_bad])
        em = c
        em_up = u - c
        em_low = c - l 
        zs = np.array([x.z.mean() for x in individuals_bad])
        uz = np.array([x.zlims[0] for x in individuals_bad])
        lz = np.array([x.zlims[1] for x in individuals_bad])
        uzerr = uz-zs
        lzerr = zs-lz 
        ax.errorbar(zs, em, ecolor='k', capsize=0, fmt='None', elinewidth=1.5,
                    yerr=np.vstack((em_low, em_up)),
                    xerr=np.vstack((lzerr, uzerr)), 
                    mfc='#ffffff', mec='#404040', zorder=6, mew=1,
                    ms=5)
        ax.scatter(zs, em, c='#ffffff', edgecolor='k',
                   s=42, zorder=6, linewidths=1.5) 

    # zg, eg, zg_lerr, zg_uerr, eg_lerr, eg_uerr = np.loadtxt('Data_new/giallongo15_emissivity.txt', unpack=True)
    
    # eg *= 1.0e24
    # eg_lerr *= 1.0e24
    # eg_uerr *= 1.0e24
    # ax.errorbar(zg, eg, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
    #             xerr=np.vstack((zg_lerr, zg_uerr)),
    #             yerr=np.vstack((eg_lerr, eg_uerr)), 
    #             zorder=3, mew=1)

    # ax.scatter(zg, eg, c='dodgerblue', edgecolor='None',
    #            label='Giallongo et al.\ 2015', marker='s',
    #            s=42, zorder=4, linewidths=1.5)

    giallongo15(ax, only21=True)
    
    e_MH15 = emissivity_MH15(z)
    ax.plot(z, e_MH15, lw=1, c='darkgreen', label='Madau and Haardt 2015', zorder=1, dashes=[1,1])

    e_HM12 = emissivity_HM12(z)
    ax.plot(z, e_HM12, lw=2, c='brown', label='Haardt and Madau 2012', zorder=3, dashes=[7,2])

    e_M17 = emissivity_Manti17(z)
    ax.plot(z, e_M17, lw=2, c='grey', label='Manti et al.\ 2017', zorder=2, dashes=[7,2])

    # Emissivity at z = 0 from Schulze et al. 2009 A&A 507 781.  This
    # number is rederived by Gabor.  See his email of 8 March 2018.
    z_Schulze09 = np.array([0.0])
    e_Schulze09 = np.array([0.0435e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_Schulze09, e_Schulze09, c='dodgerblue', edgecolor='None', marker='p',
               s=42, zorder=12, linewidths=2, label='Schulze et al.\ 2009')

    # Emissivity at z = 5 from McGreer et al. 2018 AJ 155 131.  This
    # number is rederived by Gabor.  See his email of 12 March 2018.
    z_McGreer_lerr = np.array([4.9-4.7])
    z_McGreer_uerr = np.array([5.1-4.9])
    z_McGreer18 = np.array([4.9])
    e_McGreer18 = np.array([0.6836e24]) # erg/s/Hz/Mpc^3
    ax.scatter(z_McGreer18, e_McGreer18, c='dodgerblue', edgecolor='None',
               label='McGreer et al.\ 2018', s=42, zorder=10)

    ax.errorbar(z_McGreer18, e_McGreer18, ecolor='dodgerblue', capsize=0, fmt='None', elinewidth=1.5,
                xerr=np.vstack((z_McGreer_lerr, z_McGreer_uerr)),
                zorder=10, mew=1, linewidths=1.5)
    
    
    zmin_Onoue17 = 5.5
    zmax_Onoue17 = 6.5
    emin_Onoue17 = 0.1118e24
    emax_Onoue17 = 0.1299e24
    dz_Onoue17 = zmax_Onoue17 - zmin_Onoue17
    de_Onoue17 = emax_Onoue17 - emin_Onoue17
    rect = mpatches.Rectangle((zmin_Onoue17, emin_Onoue17),
                              dz_Onoue17, de_Onoue17,
                              ec='dodgerblue', color='None',
                              lw=2, zorder=10, label='Onoue et al.\ 2017')
    ax.add_patch(rect)

    pd13(ax, only21=True)

    pd16(ax, only21=True)

    c17(ax, only21=True)

    akiyama18(ax, only21=True)

    parsa18(ax, only21=True)

    masters12(ax, only21=True)

    # bongiorno07(ax, only21=True)
    
    handles, labels = ax.get_legend_handles_labels()
    handles.append((tw18f,tw18))
    labels.append('Kulkarni et al.\ 2019 (this work; fit)')

    # myorder = [10, 14, 9, 12, 11, 13, 7, 0, 1, 2, 3, 4, 5, 6, 8, 15]
    myorder = [9, 13, 8, 11, 10, 12, 6, 0, 1, 2, 3, 4, 5, 7, 14]
    handles = [handles[x] for x in myorder]
    labels = [labels[x] for x in myorder]
    
    plt.legend(handles, labels, loc='center', fontsize=12, handlelength=3,
               frameon=False, framealpha=0.0, labelspacing=.1, #ncol=2, columnspacing=2,
               handletextpad=0.1, borderpad=0.01, scatterpoints=1, borderaxespad=1, bbox_to_anchor=[0.4,0.25])

    plt.text(0.94, 0.94, '$M_\mathrm{1450}<-21$', horizontalalignment='right',
             verticalalignment='center', transform=ax.transAxes, fontsize='16')
    
    
    plt.savefig('emissivity_21.pdf',bbox_inches='tight')
    #plt.close('all')

    return
