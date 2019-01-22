
import numpy as np
from numpy import log as log
from scipy.optimize import brentq
from scipy.special import gammainc, gammaincc, gammaln

from .convenience_functions import n_pi_func
from .convenience_functions import p as pow

# prior assumption for diffusivity inference that does not include D'.
# Should be described in the article Appendix


def zeta_mu(dim):
    """The center of the prior for the total force.
    For diffusivity inference should not depend on the diffusivity gradient.
    """
    return np.zeros(dim)


def norm2(x):
    return np.sum(x**2)


def get_D_posterior(n, zeta_t, V, V_pi, sigma2, dim, _MAP_D=False):
    """Return the diffusivity posterior as a function.
    If _MAP_D flag is supplied, returns instead a single MAP(D) value

    Input:
    V   -   (biased) variance of jumps in the current bin
    V_pi    -   (biased) variance of jumps in all other bins excluding the current one
    sigma2  -   localization error (in the units of variance)
    dim -   dimensionality of the problem
    _MAP_D  -   if True, returns MAP_D instead of the posterior

    Output:
    posterior    -   function object accepting D as the only argument
    """

    n_pi = n_pi_func(dim)
    p = pow(n, dim)
    v = 1.0 + n_pi / n * V_pi / V
    eta = np.sqrt(n_pi / (n + n_pi))
    G3 = v + eta**2 * norm2(zeta_t - zeta_mu(dim))

    if _MAP_D:
        return n * V * G3 / 2 / dim / (p + 1)

    # Conversions
    zeta_t = np.array(zeta_t)
    if sigma2 > 0:
        rel_loc_error = n * V / (2 * dim * sigma2)
    else:
        rel_loc_error = np.inf

    def posterior(D):
        """Remember gammainc is normalized to gamma"""
        min_D = sigma2 / dim
        if D <= min_D:
            ln_res = -np.inf
        else:
            ln_res = (p * log(n * V * G3 / 2 / dim / D)
                      - n * V * G3 / 2 / dim / D
                      - log(D)
                      - log(gammainc(p, rel_loc_error * G3))
                      - gammaln(p))
        return np.exp(ln_res)
    return posterior


def get_MAP_D(n, zeta_t, V, V_pi, sigma2, dim):
    return get_D_posterior(n, zeta_t, V, V_pi, sigma2, dim, _MAP_D=True)


def get_D_confidence_interval(alpha, n, zeta_t, V, V_pi, sigma2, dim):
    """Returns MAP_D and a confidence interval corresponding to confidence level alpha, i.e. the values of D giving the values [alpha/2, 1-alpha/2] for the D posterior integrals
    """

    n_pi = n_pi_func(dim)
    p = pow(n, dim)
    v = 1.0 + n_pi / n * V_pi / V
    eta = np.sqrt(n_pi / (n + n_pi))
    zeta_t = np.array(zeta_t)
    G3 = v + eta**2 * norm2(zeta_t - zeta_mu(dim))

    MAP_D = get_MAP_D(n, zeta_t, V, V_pi, sigma2, dim)

    def posterior_integral(D):
        if z <= min_D:
            intg = 0
        else:
            intg = ((gammainc(p, n * V * G3 / 2 / sigma2)
                     - gammainc(p, n * V * G3 / 2 / dim / D))
                    / gammainc(p, n * V * G3 / 2 / sigma2))
        return intg

    # %% Find root
    min_D = sigma2 / dim    # units of variance /s
    max_D_search = 1e4  # Maximal D up to which to look for a root, units of variance /s
    CI = np.ones(2) * np.nan

    for i, z in enumerate([alpha / 2, 1 - alpha / 2]):
        def solve_me(D):
            return posterior_integral(D) - z
        CI[i] = brentq(solve_me, min_D, max_D_search)

    return MAP_D, CI
