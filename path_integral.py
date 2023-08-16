from time import time
import pandas as pd
import numpy as np
import random
import sys
import math
import re
import os

'''
    Computing the correlation function only where opertor a is initially localised to x 
    , where x is an integer, and operator b is localised to some point y at time 2t, 
    where y is an integer.

    TODO: '1. maybe implement random walk here

    LATER: 1. Possible SVD for larger transfer matricies??
'''

def main():

    q, k, tspan, depth = 2, 3, 10, 6

    pertubations = [7e-08]

    start = time()

    generate_data(q,tspan,pertubations)
    
    end = time()

    print('Total time taken to run:', end-start, '\n')

def generate_data(q:int,
                  tspan:int,
                  pertubations:np.ndarray,
                  k:int = 0):

    rstr = r'DU_' + str(q) + r'_([0-9]*).csv'
    rx = re.compile(rstr)

    if k:
        path = 'data/PathIntegralTruncated'
    else:
        path = 'data/PathIntegral'

    for _, _, files in os.walk('data/FoldedTensors'):
        for file in files[:1]:

            res = rx.match(file)
            seed = res.group(1)
    
            W = np.loadtxt(f'data/FoldedTensors/DU_{q}_{seed}.csv',
                            delimiter=',',dtype='complex_')
            
            # rstr2 = f'P_{q}_' + r'([0-9e\-.]*).csv'
            # rx2 = re.compile(rstr2)
            
            for e in pertubations:

                # res2 = rx2.match(file)

                # if not res2: continue

                # e = res2.group(1)

                P = np.loadtxt(f'data/FoldedPertubations/P_{q}_{e}.csv',
                                delimiter=',',dtype='complex_')

                PW = np.einsum('ab,bc->ac',P,W).reshape(q**2,q**2,q**2,q**2)

                df = pd.DataFrame()
                err = pd.Series()

                for T in range(2*tspan+1):

                    t = float(T)/2

                    data = np.array([])
                    inds = np.array([])

                    for x in range(-T,T+1):
                        x = float(x)/2
                        inds = np.append(inds,x)
                        data = np.append(data,[path_integral(x,t,PW,k=k)])

                    s = pd.Series(data,inds,name=t)

                    df = pd.concat([df, s.to_frame().T])
                    err[t] = np.abs(sum(data))
                
                df = df.reindex(sorted(df.columns,key=lambda num: float(num)), axis=1)
                df = df.fillna(0)
                print(df,'\n')

                try:
                    df.to_csv(f'{path}/{q}_{seed}_{e}.csv', index=False)
                except:
                    os.mkdir(path)
                    df.to_csv(f'{path}/{q}_{seed}_{e}.csv', index=False)

                try:
                    err.to_csv(f'{path}/charge_conservation/{q}_{seed}_{e}.csv', index=False)
                except:
                    os.mkdir(f'{path}/charge_conservation')
                    err.to_csv(f'{path}/charge_conservation/{q}_{seed}_{e}.csv', index=False)

def generate_conefront(q:int,
                       tspan:int,
                       depth:int,
                       k:int = 0):
    
    rstr = r'DU_' + str(q) + r'_([0-9]*).csv'
    rx = re.compile(rstr)

    if k:
        path = f'data/truncated_conefront_k{k}/'
    else:
        path = 'data/complete_conefront/'

    for _, _, files in os.walk('data/FoldedTensors'):
        for file in files[:1]:

            res = rx.match(file)
            seed = res.group(1)
    
            W = np.loadtxt(f'data/FoldedTensors/DU_{q}_{seed}.csv',
                            delimiter=',',dtype='complex_')
            
            rstr2 = f'P_{q}_' + r'([0-9e\-.]*).csv'
            rx2 = re.compile(rstr2)
            
            for _, _, files in os.walk('data/FoldedPertubations'):
                for file in files:

                    res2 = rx2.match(file)

                    if not res2: continue

                    e = res2.group(1)

                    P = np.loadtxt(f'data/FoldedPertubations/P_{q}_{e}.csv',
                                    delimiter=',',dtype='complex_')

                    PW = np.einsum('ab,bc->ac',P,W).reshape(q**2,q**2,q**2,q**2)

                    df = pd.DataFrame()

                    max_dev = np.inf

                    for T in range(2*tspan+1):

                        t = float(T)/2

                        data = np.array([])
                        inds = np.array([])

                        for x in range(T-depth,T+1):
                            x = float(x)/2
                            inds = np.append(inds,x)
                            data = np.append(data,[path_integral(x,t,PW,k=k)])

                        s = pd.Series(data,inds,name=t)

                        df = pd.concat([df, s.to_frame().T])
                        df = df.fillna(0)

                        if np.abs(sum(data)) < max_dev: max_dev = sum(data)

                        print('Light cone completely computed for t = ', t, '\n')

                    print(f'\nFor a pertubation e:{e} the greatest deviation in charge conservation is: ',
                        max_dev, '\n')
                    
                    print(df,'\n')

                    try:
                        df.to_csv(path+f'heatmap_{q}_{seed}_{e}.csv')
                    except:
                        os.mkdir(path)
                        df.to_csv(path+f'heatmap_{q}_{seed}_{e}.csv')

def path_integral(x:float,
                  t:float,
                  W:np.ndarray,
                  k:int = 0):

    def transfer_matrix(W:np.ndarray, a:np.ndarray,
                        x:int, b:np.ndarray = [],
                        horizontal:bool = True,
                        terminate:bool = False,
                        X:float = 0):

        '''
            A transfer matrix can either be horizontal or vertical row of contracted
            folded tensors. 
            For the case of a horizontal transfer matrix the row can only be terminated
            either by a defect or by the operator b

            a can be like [0,1,0,0]
        '''

        if horizontal:
            direct = W[0,:,:,0]
            defect = W[:,0,:,0]
        else:
            direct = W[:,0,0,:]
            defect = W[0,:,0,:]

        if x > 1:
            for _ in range(x-2):
                a = np.einsum('ba,a->b',direct,a)

        if not terminate:
            a = np.einsum('ba,a->b',direct,a)
            return np.einsum('ba,a->b',defect,a)
        else:
            if int(2*(t+X))%2 == 0:
                a = np.einsum('ba,a->b',direct,a)
            else:
                a = np.einsum('ba,a->b',defect,a)
            return np.einsum('a,a->',b,a)
        
    def skeleton(x_h:np.ndarray, x_v:np.ndarray, W:np.ndarray,
                 a:np.ndarray, b:np.ndarray, X:float = 0):
        '''
            Computes a contribution to the path integral of the
            input skeleton diagram
        '''

        for i in range(len(x_v)):
            a = transfer_matrix(W,a,x_h[i])
            a = transfer_matrix(W,a,x_v[i],horizontal=False)

        return transfer_matrix(W,a,x_h[-1],b=b,terminate=True,X=X) if len(x_h) > len(x_v) else np.einsum('a,a->',a,b)

    a, b = np.array([0,1,0,0],dtype='complex_'), np.array([0,1,0,0],dtype='complex_')

    if x == 0 and t == 0.:
        return np.abs(np.einsum('a,a->',a,b))

    vertical_data = {}
    horizontal_data = {}

    x_h, x_v = math.ceil(t+x), math.floor(t+1-x)

    if k > x_h or k > x_v or not k:
        k = min(x_h,x_v)

    list_generator(x_v-1,vertical_data,k=k)
    list_generator(x_h,horizontal_data,k=k)

    n = 1
    sum = 0

    while n <= k:

        try:
            l1, l2 = horizontal_data[n], vertical_data[n]
            for h in l1:
                for v in l2:
                    sum += skeleton(h,v,W,a,b,X=x)
        except:pass
            
        try:
            l1, l2 = horizontal_data[n+1], vertical_data[n]
            for h in l1:
                for v in l2:
                    sum += skeleton(h,v,W,a,b,X=x)
        except:pass
                        
        try:
            l1, v = horizontal_data[1], vertical_data[0]
            for h in l1:
                sum += skeleton(h,[],W,a,b,X=x)
        except:pass

        n += 1

    return sum

def list_generator(x:int,data:dict,k:int=np.inf,
                    lists:np.ndarray=[]):
    '''
        Generates a complete set of possible lists which can
        combine to form a complete set 

        For now just taking base case of the operator a being 
        intially being localised to an integer position 
    '''

    if x == 0:
        try:
            data[len(lists)].append(lists)
        except:
            data[len(lists)] = [lists]
        return
    elif len(lists) >= k:
        return 

    for i in range(1,x+1):
        sublist = lists.copy()
        sublist.append(i)
        list_generator(x-i,data,k,sublist)

def metropolis_hastings(input:np.ndarray,x:int):

    if input[-1] != x or input[0] != 0:
        raise Exception('Input array not of correct format')
    
    for i in range(1,len(input)-1):
         if random.randrange(sys.maxsize) % 2 and input[i-1]-input[i+1] == 0:
            input[i] = 2*input[i+1] - input[i]

    return input
    
if __name__ == '__main__':
    main()