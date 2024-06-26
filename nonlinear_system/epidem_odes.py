import numpy as np
from nonlinear_system.sample_odes import ControlAffineODE
from lib.func import quad_roots

NDERIVS = 3

class UIV(ControlAffineODE):

    def __init__(self,  beta=4.71, delta=1.07, p=3.07, c=2.3):
        self.beta = beta
        self.delta = delta
        self.p_p = p
        self.c = c
        self.nderivs = NDERIVS
        super().__init__(state_dim=3, input_dim=1, output_dim=3, f=self.uiv_f, h=self.output_derivative)
    
    def uiv_f(self, t: float, x: np.ndarray):
        '''
        RHS for UIV system:

        d_x0 = - beta*x0*x2
        d_x1 = beta*x0*x2 - delta*x1
        d_x2 = p*x1 - c*x2

        '''
        rhs = np.array([
            -self.beta*x[0]*x[2],
            self.beta*x[0]*x[2] - self.delta*x[1],
            self.p_p*x[1] - self.c*x[2]
        ])
        return rhs
    
    def output_fn(self, t: float, x: np.ndarray, u: np.ndarray):
        return x[2]
    
    def output_derivative(self, t: float, x: np.ndarray, u: np.ndarray):
        '''
        Computes the output of the system and it's derivatives
        '''
        y_d = np.empty((self.nderivs,))
        y_d[0] = x[2]
        y_d[1] = self.rhs(t, x, u)[2]
        y_d[2] = self.p_p*self.beta*x[0]*x[2] - (self.c+self.delta)*y_d[1] - self.delta*self.c*x[2]
        return y_d
    
    def invert_output(self, t: float, y_d: np.ndarray, u: np.ndarray = None):
        '''
        Function that maps the output and it's derivatives to the system states
        '''
        xhat = np.array([
            (y_d[2]+(self.delta+self.c)*y_d[1]+self.delta*self.c*y_d[0])/(self.p_p*self.beta*y_d[0]),
            (y_d[1]+self.c*y_d[0])/self.p_p,
            y_d[0]
        ])
        return xhat
    
    def invert_output2(self, t: float, y_d: np.ndarray, u: np.ndarray = None):
        '''
        Function that maps the output and it's derivatives to the states [V, I, UV]
        '''
        xhat = np.array([
            y_d[0],
            (y_d[1]+self.c*y_d[0])/self.p_p,
            (y_d[2]+(self.delta+self.c)*y_d[1]+self.delta*self.c*y_d[0])/(self.p_p*self.beta)
        ])
        return xhat
    
    def bound_tf(self, y_bound):
        x2_bound = np.zeros((self.nderivs, y_bound.shape[1]))

        x2_bound[0] = y_bound[0]
        x2_bound[1] = (y_bound[1]+self.c*y_bound[0])/self.p_p
        x2_bound[2] = (y_bound[2] + (self.c+self.delta)*y_bound[1] + self.c*self.delta*y_bound[0]) / (self.p_p*self.beta)
        return x2_bound
    
    def state_tf_bound(self, x2, x2_bound):
        x_min = np.zeros(x2.shape)
        x_max = np.zeros(x2.shape)

        for i in range(x2.shape[0]):
            x_min[x2.shape[0]-1-i] = x2[i,:]-x2_bound[i,:]
            x_max[x2.shape[0]-1-i] = x2[i,:]+x2_bound[i,:]

        x_min[0] = np.minimum(x_min[0]/x_min[2], x_min[0]/x_max[2])
        x_max[0] = np.maximum(x_max[0]/x_min[2], x_max[0]/x_max[2])
        return x_min, x_max
    
    def state_tf(self, x2):
        x = np.zeros(x2.shape)
        x[2] = x2[0]
        x[1] = x2[1]
        x[0] = x2[2]/x2[0]
        return x
        
    def state_transform(self, x):
        x2 = np.zeros(x.shape)
        x2[0,:] = x[2,:]
        x2[1,:] = x[1,:]
        x2[2,:] = x[2,:]*x[0,:]
        return x2
    

class UEIV(ControlAffineODE):

    def __init__(self,  beta=4.71, delta=1.07, p=3.07, c=2.3, k=0.17):
        self.beta = beta
        self.delta = delta
        self.p_p = p
        self.c = c
        self.k = k
        self.nderivs = 4
        super().__init__(state_dim=4, input_dim=1, output_dim=4, f=self.uiv_f, h=self.output_derivative)
    
    def uiv_f(self, t: float, x: np.ndarray):
        '''
        RHS for UIV system:

        d_x0 = - beta*x0*x3
        d_x1 = beta*x0*x3 - k*x1
        d_x2 = k*x1 - delta*x2
        d_x3 = p*x2 - c*x3

        '''
        rhs = np.array([
            -self.beta*x[0]*x[3],
            self.beta*x[0]*x[3] - self.k*x[1],
            self.k*x[1] - self.delta*x[2],
            self.p_p*x[2] - self.c*x[3]
        ])
        return rhs
    
    def output_fn(self, t: float, x: np.ndarray, u: np.ndarray):
        return x[3]
    
    def output_derivative(self, t: float, x: np.ndarray, u: np.ndarray):
        '''
        Computes the output of the system and it's derivatives
        '''
        rhs = self.rhs(t, x, u)
        y_d = np.empty((self.nderivs,))
        y_d[0] = x[3]
        y_d[1] = rhs[3]
        y_d[2] = self.p_p*rhs[2] - self.c*rhs[3]
        y_d[3] = self.p_p*self.k*rhs[1] - self.p_p*(self.delta+self.c)*rhs[2] + self.c*self.c*rhs[3]
        return y_d
    
    # def invert_output(self, t: float, y_d: np.ndarray, u: np.ndarray = None):
    #     '''
    #     Function that maps the output and it's derivatives to the system states
    #     '''
    #     xhat = np.array([
    #         (y_d[2]+(self.delta+self.c)*y_d[1]+self.delta*self.c*y_d[0])/(self.p_p*self.beta*y_d[0]),
    #         (y_d[1]+self.c*y_d[0])/self.p_p,
    #         y_d[0]
    #     ])
    #     return xhat
    
class SIR(ControlAffineODE):

    def __init__(self,  mu, beta, gamma):
        self.beta = beta
        self.mu = mu
        self.gamma = gamma
        self.nderivs = 2
        super().__init__(state_dim=2, input_dim=1, output_dim=2, f=self.sir_f, h=self.output_derivative)
    
    def sir_f(self, t: float, x: np.ndarray):
        '''
        RHS for SIR system:

        d_x0 = mu - mu*x0 - beta*x0*x1
        d_x1 = beta*x0*x1 - (mu+gamma)*x1

        '''
        rhs = np.array([
            self.mu - self.mu*x[0] - self.beta*x[0]*x[1],
            self.beta*x[0]*x[1] - (self.mu + self.gamma)*x[1]
        ])
        return rhs
    
    def output_fn(self, t: float, x: np.ndarray, u: np.ndarray):
        return self.beta*x[0]*x[1]
    
    def output_derivative(self, t: float, x: np.ndarray, u: np.ndarray):
        '''
        Computes the output of the system and it's derivatives
        '''
        y_d = np.empty((self.nderivs,))
        y_d[0] = self.beta*x[0]*x[1]
        y_d[1] = self.beta*(x[0]*self.rhs(t, x, u)[1]+x[1]*self.rhs(t, x, u)[0])
        return y_d
    
    def invert_output(self, t: float, y_d: np.ndarray, u: np.ndarray = None):
        '''
        Function that maps the output and it's derivatives to the system states
        '''
        a = self.beta*(self.mu-y_d[0])
        b = -(2*self.mu+self.gamma)*y_d[0]-y_d[1]
        c = y_d[0]**2

        sol1, sol2 = quad_roots(a,b,c)
        sol = sol1 if np.max(sol1)<=1 and np.min(sol1)>=0 else sol2
        xhat = np.array([
            y_d[0]/(self.beta*sol),
            sol
        ])
        return xhat
    
class SIR_t(ControlAffineODE):

    def __init__(self,  mu, beta, gamma, nu, w):
        self.beta = beta
        self.mu = mu
        self.gamma = gamma
        self.nu = nu
        self.w = w
        self.nderivs = 2
        super().__init__(state_dim=2, input_dim=1, output_dim=2, f=self.sir_f, h=self.output_derivative)
    
    def sir_f(self, t: float, x: np.ndarray):
        '''
        RHS for SIR system:

        d_x0 = mu - mu*x0 - beta*x0*x1
        d_x1 = beta*x0*x1 - (mu+gamma)*x1

        '''
        beta = self.beta*(1+self.nu*np.cos(self.w*t))
        rhs = np.array([
            self.mu - self.mu*x[0] - beta*x[0]*x[1],
            beta*x[0]*x[1] - (self.mu + self.gamma)*x[1]
        ])
        return rhs
    
    def output_fn(self, t: float, x: np.ndarray, u: np.ndarray):
        return self.self.beta*(1+self.nu*np.cos(self.w*t))*x[0]*x[1]
    
    def output_derivative(self, t: float, x: np.ndarray, u: np.ndarray):
        '''
        Computes the output of the system and it's derivatives
        '''
        beta = self.beta*(1+self.nu*np.cos(self.w*t))
        y_d = np.empty((self.nderivs,))
        y_d[0] = beta*x[0]*x[1]
        y_d[1] = beta*(x[0]*self.rhs(t, x, u)[1] + x[1]*self.rhs(t, x, u)[0]) + self.beta*(-self.nu*self.w*np.sin(self.w*t))*x[0]*x[1]
        return y_d
    
    def invert_output(self, t: float, y_d: np.ndarray, u: np.ndarray = None):
        '''
        Function that maps the output and it's derivatives to the system states
        '''
        beta = self.beta*(1+self.nu*np.cos(self.w*t))
        beta_dot = -self.beta*self.nu*self.w*np.sin(self.w*t)

        a = beta*(self.mu-y_d[0])
        b = -(2*self.mu+self.gamma)*y_d[0]-y_d[1] + y_d[0]*beta_dot/beta 
        c = y_d[0]**2

        sol1, sol2 = quad_roots(a,b,c)
        sol = sol1 if np.max(sol1)<=1 and np.min(sol1)>=0 else sol2
        xhat = np.array([
            y_d[0]/(beta*sol),
            sol
        ])
        return xhat