
from SimpleCV.base import *
import scipy.signal as sps
import scipy.optimize as spo
import copy


class LineScan(list):
    """
    **SUMMARY**

    A line scan is a one dimensional signal pulled from the intensity
    of a series of a pixels in an image. LineScan allows you to do a series
    of operations just like on an image class object. You can also treat the
    line scan as a python list object. A linescan object is automatically
    generated by calling ImageClass.getLineScan on an image. You can also
    roll your own by declaring a LineScan object and passing the constructor
    a 1xN list of values.

    **EXAMPLE**

    >>>> import matplotlib.pyplot as plt
    >>>> img = Image('lenna')
    >>>> s = img.getLineScan(y=128)
    >>>> ss = s.smooth()
    >>>> plt.plot(s)
    >>>> plt.plot(ss)
    >>>> plt.show()
    """
    pointLoc = None
    image = None

    def __init__(self,*args,**kwargs):
        list.__init__(self,*args)
        self.image = None
        self.pt1 = None
        self.pt2 = None 
        for key in kwargs:
            if key == 'pointLocs':
                if kwargs[key] is not None:
                    self.pointLoc = kwargs[key]
            if key == 'image':
                if kwargs[key] is not None:
                    self.img = kwargs[key]            
            if key == 'pt1':
                if kwargs[key] is not None:
                    self.pt1 = kwargs[key]
            if key == 'pt2':
                if kwargs[key] is not None:
                    self.pt2 = kwargs[key]
                    
        if(self.pointLoc is None):
            self.pointLoc = zip(range(0,len(self)),range(0,len(self)))
 
    def __getitem__(self,key):
        """
        **SUMMARY**

        Returns a LineScan when sliced. Previously used to
        return list. Now it is possible to use LineScanm member
        functions on sub-lists

        """
        if type(key) is types.SliceType: #Or can use 'try:' for speed
            return LineScan(list.__getitem__(self, key))
        else:
            return list.__getitem__(self,key)
        
    def __getslice__(self, i, j):
        """
        Deprecated since python 2.0, now using __getitem__
        """
        return self.__getitem__(slice(i,j))


    def smooth(self,degree=3):
        """
        **SUMMARY**

        Perform a Gasusian simple smoothing operation on the signal. 
        
        **PARAMETERS**

        * *degree* - The degree of the fitting function. Higher degree means more smoothing.        
        
        **RETURNS**

        A smoothed LineScan object. 
       
        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> plt.plot(sl)
        >>>> plt.plot(sl.smooth(7))
        >>>> plt.show()

        **NOTES** 
        Cribbed from http://www.swharden.com/blog/2008-11-17-linear-data-smoothing-in-python/
        """
        window=degree*2-1  
        weight=np.array([1.0]*window)  
        weightGauss=[]  
        for i in range(window):  
            i=i-degree+1  
            frac=i/float(window)    
            gauss=1/(np.exp((4*(frac))**2))    
            weightGauss.append(gauss) 
        weight=np.array(weightGauss)*weight   
        smoothed=[0.0]*(len(self)-window)  
        for i in range(len(smoothed)):  
            smoothed[i]=sum(np.array(self[i:i+window])*weight)/sum(weight)
        # recenter the signal so it sits nicely on top of the old
        front = self[0:(degree-1)]
        front += smoothed
        front += self[-1*degree:]
        retVal = LineScan(front,image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        #retVal.image = self.image
        #retVal.pointLoc = self.pointLoc
        return retVal

    def normalize(self):
        """
        **SUMMARY**
        
        Normalize the signal so the maximum value is scaled to one.
        
        **RETURNS**

        A normalized scanline object.
        
        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> plt.plot(sl)
        >>>> plt.plot(sl.normalize())
        >>>> plt.show()

        """
        temp = np.array(self, dtype='float32')
        temp = temp / np.max(temp)
        retVal = LineScan(list(temp[:]),image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)                           
        #retVal.image = self.image
        #retVal.pointLoc = self.pointLoc
        return retVal

    def scale(self,value_range=(0,1)):
        """
        **SUMMARY**
       
        Scale the signal so the maximum and minimum values are
        all scaled to the values in value_range. This is handy
        if you want to compare the shape of two signals that
        are scaled to different ranges.
        
        **PARAMETERS**

        * *value_range* - A tuple that provides the lower and upper bounds
                          for the output signal. 
         
        **RETURNS**

        A scaled LineScan object. 
        
        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> plt.plot(sl)
        >>>> plt.plot(sl.scale(value_range(0,255)))
        >>>> plt.show()

        **SEE ALSO**

        """        
        temp = np.array(self, dtype='float32')
        vmax = np.max(temp)
        vmin = np.min(temp)
        a = np.min(value_range)
        b = np.max(value_range)
        temp = (((b-a)/(vmax-vmin))*(temp-vmin))+a
        retVal = LineScan(list(temp[:]),image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)                                
        #retVal.image = self.image
        #retVal.pointLoc = self.pointLoc
        return retVal

    def minima(self):
        """
        **SUMMARY**

        The function the global minima in the line scan.         
        
        **RETURNS**

        Returns a list of tuples of the format:
        (LineScanIndex,MinimaValue,(image_position_x,image_position_y))      

        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> minima = sl.smooth().minima()
        >>>> plt.plot(sl)
        >>>> for m in minima:
        >>>>    plt.plot(m[0],m[1],'ro')
        >>>> plt.show()

        """        
        # all of these functions should return
        # value, index, pixel coordinate
        # [(index,value,(pix_x,pix_y))...]        
        minvalue = np.min(self)
        idxs = np.where(np.array(self)==minvalue)[0]
        minvalue = np.ones((1,len(idxs)))*minvalue # make zipable
        minvalue = minvalue[0]
        pts = np.array(self.pointLoc)
        pts = pts[idxs]
        pts = [(p[0],p[1]) for p in pts] # un numpy this 
        return zip(idxs,minvalue,pts)
        
    def maxima(self):
        """
        **SUMMARY**

        The function finds the global maxima in the line scan.
        
        **RETURNS**

        Returns a list of tuples of the format:
        (LineScanIndex,MaximaValue,(image_position_x,image_position_y))      

        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> maxima = sl.smooth().maxima()
        >>>> plt.plot(sl)
        >>>> for m in maxima:
        >>>>    plt.plot(m[0],m[1],'ro')
        >>>> plt.show()

        """        

        # all of these functions should return
        # value, index, pixel coordinate
        # [(index,value,(pix_x,pix_y))...]        
        maxvalue = np.max(self)
        idxs = np.where(np.array(self)==maxvalue)[0]
        maxvalue = np.ones((1,len(idxs)))*maxvalue # make zipable
        maxvalue = maxvalue[0]
        pts = np.array(self.pointLoc)
        pts = pts[idxs]
        pts = [(p[0],p[1]) for p in pts] # un numpy 
        return zip(idxs,maxvalue,pts)
 
    def derivative(self):
        """
        **SUMMARY**
        
        This function finds the discrete derivative of the signal.
        The discrete derivative is simply the difference between each
        succesive samples. A good use of this function is edge detection
        
        **RETURNS**

        Returns the discrete derivative function as a LineScan object.
        
        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> plt.plot(sl)
        >>>> plt.plot(sl.derivative())
        >>>> plt.show()

        """
        temp = np.array(self,dtype='float32')
        d = [0]
        d += list(temp[1:]-temp[0:-1])
        retVal = LineScan(d,image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        #retVal.image = self.image
        #retVal.pointLoc = self.pointLoc
        return retVal
    
    def localMaxima(self):
        """
        **SUMMARY**

        The function finds local maxima in the line scan. Local maxima
        are defined as points that are greater than their neighbors to
        the left and to the right.         
        
        **RETURNS**

        Returns a list of tuples of the format:
        (LineScanIndex,MaximaValue,(image_position_x,image_position_y))      

        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> maxima = sl.smooth().maxima()
        >>>> plt.plot(sl)
        >>>> for m in maxima:
        >>>>    plt.plot(m[0],m[1],'ro')
        >>>> plt.show()

        """        
        temp = np.array(self)
        idx = np.r_[True, temp[1:] > temp[:-1]] & np.r_[temp[:-1] > temp[1:], True]
        idx = np.where(idx==True)[0]
        values = temp[idx]
        pts = np.array(self.pointLoc)
        pts = pts[idx]
        pts = [(p[0],p[1]) for p in pts] # un numpy
        return zip(idx,values,pts)

        
    def localMinima(self):
        """""
        **SUMMARY**

        The function the local minima in the line scan. Local minima
        are defined as points that are less than their neighbors to
        the left and to the right. 
        
        **RETURNS**

        Returns a list of tuples of the format:
        (LineScanIndex,MinimaValue,(image_position_x,image_position_y))      

        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> minima = sl.smooth().minima()
        >>>> plt.plot(sl)
        >>>> for m in minima:
        >>>>    plt.plot(m[0],m[1],'ro')
        >>>> plt.show()

        """        
        temp = np.array(self)
        idx = np.r_[True, temp[1:] < temp[:-1]] & np.r_[temp[:-1] < temp[1:], True]
        idx = np.where(idx==True)[0]
        values = temp[idx]
        pts = np.array(self.pointLoc)
        pts = pts[idx]
        pts = [(p[0],p[1]) for p in pts] # un numpy
        return zip(idx,values,pts)

    def resample(self,n=100):
        """
        **SUMMARY**

        Resample the signal to fit into n samples. This method is
        handy if you would like to resize multiple signals so that
        they fit together nice. Note that using n < len(LineScan)
        can cause data loss. 
        
        **PARAMETERS**

        * *n* - The number of samples to resample to. 
        
        **RETURNS**

        A LineScan object of length n. 
        
        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> plt.plot(sl)
        >>>> plt.plot(sl.resample(100))
        >>>> plt.show()

        """
        signal = sps.resample(self,n)
        pts = np.array(self.pointLoc)
        # we assume the pixel points are linear
        # so we can totally do this better manually 
        x = linspace(pts[0,0],pts[-1,0],n)
        y = linspace(pts[0,1],pts[-1,1],n)
        pts = zip(x,y)
        retVal = LineScan(list(signal),image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        #retVal.image = self.image
        #retVal.pointLoc = pts
        return retVal


    # this needs to be moved out to a cookbook or something
    #def linear(xdata,m,b):
    #    return m*xdata+b

    # need to add polyfit too
    #http://docs.scipy.org/doc/numpy/reference/generated/numpy.polyfit.html
    def fitToModel(self,f,p0=None):
        """
        **SUMMARY**

        Fit the data to the provided model. This can be any arbitrary
        2D signal. Return the data of the model scaled to the data. 
        
        
        **PARAMETERS**

        * *f* - a function of the form f(x_values, p0,p1, ... pn) where
                p is parameter for the model.

        * *p0* - a list of the initial guess for the model parameters. 
        
        **RETURNS**

        A LineScan object where the fitted model data replaces the
        actual data. 

        
        **EXAMPLE**

        >>>> def aLine(x,m,b):
        >>>>     return m*x+b
        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> fit = sl.fitToModel(aLine)
        >>>> plt.plot(sl)
        >>>> plt.plot(fit)
        >>>> plt.show()

        """
        yvals = np.array(self,dtype='float32')
        xvals = range(0,len(yvals),1)
        popt,pcov = spo.curve_fit(f,xvals,yvals,p0=p0)
        yvals = f(xvals,*popt)
        retVal = LineScan(list(yvals),image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        return retVal


    def getModelParameters(self,f,p0=None):
        """
        **SUMMARY**

        Fit a model to the data and then return 
        
        **PARAMETERS**

        * *f* - a function of the form f(x_values, p0,p1, ... pn) where
                p is parameter for the model.

        * *p0* - a list of the initial guess for the model parameters. 
        
        **RETURNS**

        The model parameters as a list. For example if you use a line
        model y=mx+b the function returns the m and b values that fit
        the data. 
        
        **EXAMPLE**

        >>>> def aLine(x,m,b):
        >>>>     return m*x+b
        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> p = sl.getModelParameters(aLine)
        >>>> print p

        """
        yvals = np.array(self,dtype='float32')
        xvals = range(0,len(yvals),1)
        popt,pcov = spo.curve_fit(f,xvals,yvals,p0=p0)
        return popt

    def convolve(self,kernel):
        """
        **SUMMARY**

        Convolve the line scan with a one dimenisional kernel stored as
        a list. This allows you to create an arbitrary filter for the signal.
        
        **PARAMETERS**

        * *kernel* - An Nx1 list or np.array that defines the kernel.
        
        **RETURNS**

        A LineScan feature with the kernel applied. We crop off
        the fiddly bits at the end and the begining of the kernel
        so everything lines up nicely. 
        
        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> smooth_kernel = [0.1,0.2,0.4,0.2,0.1]
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> out = sl.convolve(smooth_kernel)
        >>>> plt.plot(sl)
        >>>> plt.plot(out)
        >>>> plt.show()

        **SEE ALSO**

        """        
        k = len(kernel)
        if( k%2 == 0):
            kl = (k/2)-1
            kt = k/2
        else:
            kl = (k-1)/2
            kt = kl
        out = np.convolve(self,np.array(kernel,dtype='float32'))
        out = out[kt:-1*kl]
        retVal = LineScan(out,image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        #retVal.image = self.image
        #retVal.pointLoc = self.pointLoc
        return retVal

    def fft(self):
        """
        **SUMMARY**

        Perform a Fast Fourier Transform on the line scan and return
        the FFT output and the frequency of each value. 
        
        
        **RETURNS**

        The FFT as a numpy array of irrational numbers and a one dimensional
        list of frequency values. 
        
        **EXAMPLE**

        >>>> import matplotlib.pyplot as plt
        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(y=128)
        >>>> fft,freq = sl.fft()
        >>>> plt.plot(freq,fft.real,freq,fft.imag)
        >>>> plt.show()

        """
        signal = np.array(self,dtype='float32')
        fft = np.fft.fft(signal)
        freq = np.fft.fftfreq(len(signal))
        return (fft,freq)
        
        
    def ifft(self,fft):
        """
        **SUMMARY**

        Perform an inverse fast Fourier transform on the provided
        irrationally valued signal and return the results as a
        LineScan. 
        
        
        **PARAMETERS**

        * *fft* - A one dimensional numpy array of irrational values
                  upon which we will perform the IFFT.
        
        **RETURNS**
        
        A LineScan object of the reconstructed signal.
        
        **EXAMPLE**

        >>>> img = Image('lenna')
        >>>> sl = img.getLineScan(pt1=(0,0),pt2=(300,200))
        >>>> fft,frq = sl.fft()
        >>>> fft[30:] = 0 # low pass filter
        >>>> sl2 = sl.ifft(fft)
        >>>> import matplotlib.pyplot as plt
        >>>> plt.plot(sl)
        >>>> plt.plot(sl2)
        """
        signal = np.fft.ifft(fft)
        retVal = LineScan(signal.real)
        retVal.image = self.image
        retVal.pointLoc = self.pointLoc
        return retVal

    def createEmptyLUT(self,defaultVal=-1):
        """
        Create an empty look up table.

        If default value is what the lut is intially filled with
        if defaultVal == 0
            the array is all zeros.
        if defaultVal > 0
            the array is set to default value. Clipped to 255.
        if defaultVal < 0
            the array is set to the range [0,255]
        if defaultVal is a tuple of two values:
            we set stretch the range of 0 to 255 to match
            the range provided.
        """
        lut = None
        if( isinstance(defaultVal,list) or
            isinstance(defaultVal,tuple)):
            start = np.clip(defaultVal[0],0,255)
            stop = np.clip(defaultVal[1],0,255)
            lut = np.around(np.linspace(start,stop,256),0)
            lut = np.array(lut,dtype='uint8')
            lut = lut.tolist()            
        elif( defaultVal == 0 ):
            lut = np.zeros([1,256]).tolist()[0]
        elif( defaultVal > 0 ):
            defaultVal = np.clip(defaultVal,1,255)
            lut = np.ones([1,256])*defaultVal
            lut = np.array(lut,dtype='uint8')
            lut = lut.tolist()[0]
        elif( defaultVal < 0 ):
            lut = np.linspace(0,256,256)
            lut = np.array(lut,dtype='uint8')
            lut = lut.tolist()
        return lut
            
    def fillLUT(self,lut,idxs,value=255):
        # for the love of god keep this small
        # for some reason isInstance is being persnickety
        if(idxs.__class__.__name__  == 'Image' ):
            npg = idxs.getGrayNumpy()
            npg = npg.reshape([npg.shape[0]*npg.shape[1]])
            idxs = npg.tolist()
        value = np.clip(value,0,255)
        for idx in idxs:
            if(idx >= 0 and idx < len(lut)):
                lut[idx]=value
        return lut

    def threshold(self,threshold=128,invert=False):
        out = []
        high = 255
        low = 0
        if( invert ):
            high = 0
            low = 255
        for pt in self:
            if( pt < threshold ):
                out.append(low)
            else:
                out.append(high)
        retVal = LineScan(out,image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        return retVal
        
    def invert(self):
        out = []
        for pt in self:
            out.append(255-pt)
        retVal = LineScan(out,image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        return retVal
        
    def median(self,sz=5):
        """
        Do a sliding median filter of size with a window size equal to size
        Size must be odd
        """
        if( sz%2==0 ):
            sz = sz+1
        skip = int(np.floor(sz/2))
        out = self[0:skip]
        vsz = len(self)
        for idx in range(skip,vsz-skip):
            val = np.median(self[(idx-skip):(idx+skip)])
            out.append(val)
        for pt in self[-1*skip:]:
            out.append(pt)
        retVal = LineScan(out,image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        return retVal
    
    def findFirstIdxEqualTo(self,value=255):
        vals = np.where(np.array(self)==value)[0]
        retVal = None
        if( len(vals) > 0 ):
            retVal = vals[0]
        return retVal
        
    def findLastIdxEqualTo(self,value=255):
        vals = np.where(np.array(self)==value)[0]
        retVal = None
        if( len(vals) > 0 ):
            retVal = vals[-1]
        return retVal

    def applyLUT(self,lut):
        """
        Apply a look up table to the signal.
        
        * *lut* an array of of length 256, the array elements are the values
          that are replaced via the lut
        """
        out = []
        for pt in self:
            out.append(lut[pt])
        retVal = LineScan(out,image=self.image,pointLoc=self.pointLoc,pt1=self.pt1,pt2=self.pt2)
        return retVal
