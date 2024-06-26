from nonlinear_system.ct_system import ContinuousTimeSystem
from nonlinear_system.sample_odes import Integrator
import numpy as np
import matplotlib.pyplot as plt

'''
Sample code to simulate a continuous time integrator system using the objects in this repo

    dx/dt = f(t,x,u)
    y(t) = h(t,x,u)

ControlAffineODE type objects holds the f and g functions, as well as n,m,p dimension variables

ContinuousTimeSystem type object takes as input an ODE, initial state, time step etc to generate
solution trajectories to the ODE
'''

# Cntroller Action
def control_input(t, y):
    return -10.0*y[0] - 10.0*y[1]


n = 2  # system state dimension
m = 1  # control input dimension
num_steps = 10000

x = np.empty((n, num_steps))
y = np.empty((n, num_steps))
u = np.empty((m, num_steps-1))
time = np.zeros((num_steps,))
x0 = np.random.uniform(low=-1.0, high=1.0, size=n)  # generate a random initial state
x[:, 0] = x0

ode = Integrator(n) # use n-dimensional Integrator (built-in) as ODE
sys = ContinuousTimeSystem(ode, x0=x0, dt=0.001) # create system using ODE
y[:, 0] = sys.y

print("Initialized CT System object.")

for t in range(1, num_steps):
    u[:, t-1] = control_input(sys.t, y[:, t-1])
    x[:, t], y[:, t] = sys.step(u[:, t-1])
    time[t] = sys.t
    # print(f'Completed timestep {t}, t = {sys.t:.1e}, state = {sys.x}')


f = plt.figure(figsize=(12, 12))
x0_plot = f.add_subplot((221))
x1_plot = f.add_subplot((222))
traj_plot = f.add_subplot((223))
u_plot = f.add_subplot((224))

x0_plot.plot(time, x[0, :], linewidth=2.0, c='blue')
x0_plot.set_xlabel('time (s)')
x0_plot.set_ylabel('x[0]')
x0_plot.grid()

x1_plot.plot(time, x[1, :], linewidth=2.0, c='blue')
x1_plot.set_xlabel('time (s)')
x1_plot.set_ylabel('x[1]')
x1_plot.grid()

traj_plot.plot(x[0, :], x[1, :], linewidth=2.0, c='blue')
traj_plot.scatter(x[0, 0], x[1, 0], s=50, marker='*', c='red')
# traj_plot.set_xlim(-1.0, 1.0)
# traj_plot.set_ylim(-1.0, 1.0)
traj_plot.set_xlabel('x[0]')
traj_plot.set_ylabel('x[1]')
traj_plot.grid()

u_plot.plot(time[1:], u[0, :], linewidth=2.0, c='red')
u_plot.set_xlabel('time (s)')
u_plot.set_ylabel('u')
u_plot.grid()

plt.show()
