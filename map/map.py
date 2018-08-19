from scipy.ndimage import gaussian_filter1d
import numpy as np

def upsampled_kernel(nclust, sig, upsamp):
    xs = np.arange(0,nclust)
    xn = np.linspace(0, nclust-1, nclust * upsamp)
    d0 = (xs[:,np.newaxis] - xs[np.newaxis,:])**2;
    d1 = (xn[:,np.newaxis] - xs[np.newaxis,:])**2;
    K0 = np.exp(-1*d0/sig)
    K1 = np.exp(-1*d1/sig)
    Km = K1 @ np.linalg.inv(K0 + 0.001 * np.eye(nclust));
    return Km

def map(S, ops=None, u=None, sv=None):
    if ops is None:
        ops = {'nclust': 30, # number of clusters
               'iPC': np.arange(0,200).astype(np.int32), # number of PCs to use
               'upsamp': 100, # upsampling factor for embedding position
               'sigUp': 1 # standard deviation for upsampling
               }

    S = S - S.mean(axis=1)[:,np.newaxis]
    if (u is None) or (sv is None):
        # compute svd and keep iPC's of data
        u,sv,v = np.linalg.svd(S, full_matrices=0)
        isort = np.argsort(u[:,0]).astype(np.int32)
    v = u.T @ S

    iPC = ops['iPC']
    S = u[:,iPC] @ np.diag(sv[iPC])
    NN,nPC = S.shape
    nclust = ops['nclust']
    nn = np.floor(NN/nclust) # number of neurons per cluster
    iclust = np.zeros((NN,),np.int32)
    # initial cluster assignments based on 1st PC weights
    iclust[isort] = np.floor(np.arange(0,NN)/nn).astype(np.int32)
    iclust[iclust>nclust] = nclust
    # annealing schedule for embedding
    sig_anneal = np.concatenate((np.linspace(nclust/10,1,50),np.ones((50,),np.float32)), axis=0)

    for sig in sig_anneal:
        V = np.zeros((nPC,nclust), np.float32)
        # compute average activity of each cluster
        for j in range(0,nclust):
            iin = iclust==j
            V[:,j] = S[iin,:].sum(axis=0)
        V = gaussian_filter1d(V,sig,axis=1,mode='reflect') # smooth activity across clusters
        V /= ((V**2).sum(axis=0)[np.newaxis,:])**0.5 # normalize columns to unit norm
        cv = S @ V # reproject onto activity across neurons
        # recompute best clusters
        iclust = np.argmax(cv, axis=1)
        cmax = np.amax(cv, axis=1)

    Km = upsampled_kernel(nclust,ops['sigUp'],ops['upsamp'])
    iclustup = np.argmax(cv @ Km.T, axis=1)
    isort = np.argsort(iclustup)
    vsmooth = V.T @ v[iPC,:]
    return isort, vsmooth

def run_map(S,ops=None):
    isort2 = map(S.T,ops)
    Sm = S - S.mean(axis=1)
    Sm = gaussian_filter1d(Sm,5,axis=1)
    isort1 = map(Sm,ops)
    ns = 0.02 * Sm.shape[0]
    Sm = gaussian_filter1d(Sm[isort1,:],ns,axis=1)
    return isort1,isort2,Sm,V
