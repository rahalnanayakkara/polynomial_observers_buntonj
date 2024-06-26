from nonlinear_system.ct_system import ContinuousTimeSystem
from nonlinear_system.sample_odes import ControlAffineODE
from moving_polyfit.moving_ls import PolyEstimator
import numpy as np
import matplotlib.pyplot as plt


sampling_dt = 1.0  # sampling timestep
integration_per_sample = 500  # how many integration timesteps should we take between output samples?
integration_dt = sampling_dt/integration_per_sample
num_sampling_steps = 40
num_integration_steps = num_sampling_steps*integration_per_sample

mid_t = 0.0  # sampling_dt*num_sampling_steps/2.0
f = 0.25*np.pi/sampling_dt
mag = 1.0
verbose = False


def phi(t, x):
    return mag*np.sin(f*t)


def dphidt(t, x):
    return f*mag*np.cos(f*t)


def rhs_f(t, x):
    '''
    RHS for n-dimensional integrator ODE
    dx[i]/dt = x[i+1]
    dx[n]/dt = phi(x)
    '''
    rhs = np.roll(x, -1)
    rhs[-1] = phi(t, x)
    return rhs


def output_fn(t, x, u):
    return x[0]


def control_input(t, y):
    return 0.0


n = 2  # system state dimension
m = 1  # control input dimension
p = 1  # output dimension

d = 4  # degree of estimation polynomial
N = 10  # number of samples
estimator = PolyEstimator(d, N, sampling_dt)

x = np.empty((n, num_integration_steps))
y = np.empty((p, num_integration_steps))

y_samples = np.empty((d, num_sampling_steps))   # sampled true output and it's d derivatives
x_samples = np.empty((n, num_sampling_steps))
u = np.empty((m, num_sampling_steps-1))

theta = np.empty((d+1, num_sampling_steps)) # coefficients of fitted polynomial
dphi_hat = np.empty((num_sampling_steps,))
yhat = np.empty((d, num_sampling_steps))    # estimated output and it's d derivatives

y_true = np.zeros((d, num_integration_steps))   # true output and it's d derivatives

integration_time = np.zeros((num_integration_steps,))
sampling_time = np.zeros((num_sampling_steps,))
np.random.seed(2)
x0 = np.array([0.0, -mag/f])
x[:, 0] = x0
x_samples[:, 0] = x0

ode = ControlAffineODE(state_dim=n, input_dim=m, output_dim=p, f=rhs_f, h=output_fn)
sys = ContinuousTimeSystem(ode, x0=x0, dt=integration_dt)

y[:, 0] = sys.y
y_samples[0, 0] = sys.y
y_true[0, 0] = sys.y

pols = []

print("Initialized CT system object.")


for t in range(1, num_sampling_steps):
    # select the control input
    u[:, t-1] = control_input(sys.t, y[:, t-1])

    # integrate forward in time
    for i in range(integration_per_sample):
        # compute the right "in between" index
        idx = t*integration_per_sample + i
        x[:, idx], y[:, idx] = sys.step(u[:, t-1])
        integration_time[idx] = sys.t

    # extract real values of output and its derivatives
        for j in range(sys.n):
            y_true[j, idx] = x[j, idx]
        y_true[sys.n, idx] = phi(sys.t, x[:, idx])
        y_true[sys.n+1, idx] = dphidt(sys.t, x[:, idx])

    # sample the system
    sampling_time[t] = sys.t
    y_samples[0, t], x_samples[:, t] = sys.y, sys.x

    for i in range(sys.n):
        y_samples[i, t] = x_samples[i, t]
    y_samples[sys.n, t] = phi(sys.t, x_samples[:, t])
    y_samples[sys.n+1, t] = dphidt(sys.t, x_samples[:, t])

    # estimate with polyfit (Need to reach at least N-1 samples first)
    if t >= N-1:
        # fit polynomial
        theta[:, t] = estimator.fit(y_samples[0, t-N+1:t+1])    # store polynomial coefficients
        pols.append((t, estimator.polynomial.copy()))   # store polynomials for later plotting

        # estimate with polynomial derivatives at endpoint
        for i in range(d):
                yhat[i, t] = estimator.differentiate((N-1)*sampling_dt, i)
    else:
        theta[:, t] = 0.0
        yhat[:, t] = 0.0

    if verbose:
        print(f'Completed timestep {t}, t = {sys.t:.1e}, state = {sys.x}')


f = plt.figure(figsize=(12, 8))
x0_plot = f.add_subplot((221))
x1_plot = f.add_subplot((222))
traj_plot = f.add_subplot((223))
u_plot = f.add_subplot((224))

x0_plot.plot(integration_time, x[0, :], linewidth=2.0, c='blue', label='truth')
x0_plot.plot(sampling_time[N:], yhat[0, N:], linewidth=2.0, c='red', linestyle='dashed', label='estimate')
x0_plot.scatter(sampling_time, y_samples[0, :], s=50, marker='x', c='blue', label='samples')
x0_plot.set_xlabel('time (s)')
x0_plot.set_ylabel('x1(t)')
x0_plot.legend(loc='upper right')
x0_plot.grid()

x1_plot.plot(integration_time, x[1, :], linewidth=2.0, c='blue', label='truth')
x1_plot.plot(sampling_time[N:], yhat[1, N:], linewidth=2.0, c='red', linestyle='dashed', label='estimate')
x1_plot.scatter(sampling_time, y_samples[1, :], s=50, marker='x', c='blue', label='samples')
x1_plot.set_xlabel('time (s)')
x1_plot.set_ylabel('x2(t)')
x1_plot.legend(loc='upper right')
x1_plot.grid()

traj_plot.plot(x[0, :], x[1, :], linewidth=2.0, c='blue', label='truth')
traj_plot.plot(yhat[0, N:], yhat[1, N:], linewidth=2.0, c='red', linestyle='dashed', label='estimate')
traj_plot.scatter(x[0, 0], x[1, 0], s=50, marker='*', c='blue')
traj_plot.scatter(yhat[0, N], yhat[1, N], s=50, marker='*', c='red')
traj_plot.scatter(x_samples[0, :], x_samples[1, :], s=50, marker='x', c='blue')
marg = 0.1
# traj_plot.set_xlim(x[0, :].min()-marg, x[0, :].max()+marg)
# traj_plot.set_ylim(x[1, :].min()-marg, x[1, :].max()+marg)
traj_plot.set_xlabel('x1')
traj_plot.set_ylabel('x2')
traj_plot.legend(loc='upper right')
traj_plot.grid()

u_plot.plot(sampling_time[1:], u[0, :], linewidth=2.0, c='red')
u_plot.set_xlabel('time (s)')
u_plot.set_ylabel('u')
u_plot.grid()

f.tight_layout()

f2 = plt.figure(figsize=(15, 6))
thetas_plot = f2.add_subplot(131)

for i in range(d):
    thetas_plot.plot(sampling_time[N:], theta[i, N:], linewidth=2.0, label=f'Theta[{i}]')
thetas_plot.set_ylim(-1, 1)
thetas_plot.legend(loc='upper right')
thetas_plot.grid()

est_plot = f2.add_subplot(132)
est_plot.plot(integration_time[N:], y_true[3, N:], linewidth=2.0, c='blue', label='truth')
est_plot.plot(sampling_time[N:], yhat[3, N:], linewidth=2.0, c='red', label='estimate')
est_plot.set_ylabel('d/dt phi(t)')
est_plot.legend(loc='upper right')
est_plot.grid()

yhat_plot = f2.add_subplot(133)
colors = ['red', 'blue', 'green', 'orange', 'pink']
for i in range(d):
    kwargs = {
        'label': f'{i}th derivative error',
        'linewidth': 2.0,
        'color': colors[i]
    }
    yhat_plot.plot(sampling_time[N:], np.abs(yhat[i, N:]-y_samples[i, N:]), **kwargs)
yhat_plot.legend(loc='upper right')
yhat_plot.grid()
yhat_plot.set_title('Output signal estimation errors')

f2.tight_layout()

f3 = plt.figure("Outputs", figsize=(12,8))
for i in range(d):
    fig_plot = f3.add_subplot(2,d//2,i+1)
    fig_plot.plot(integration_time, y_true[i,:], label="True")
    fig_plot.scatter(sampling_time, y_samples[i,:], c='orange', label="Samples")
    fig_plot.plot(sampling_time, yhat[i,:], label="Estimated")
    fig_plot.grid()
    fig_plot.legend()
    fig_plot.set_ylim(y_true[i,:].min()-marg, y_true[i,:].max()+marg)
    fig_plot.set_xlabel("time (s)")
    fig_plot.set_ylabel(f"$y^{i}(t)$")
f3.tight_layout()


# f4 = plt.figure("Polynomial Fitting", figsize=(12,8))
# ax4 = f4.add_subplot(111)
# ax4.plot(integration_time, y_true[1,:], label="True")
# ax4.scatter(sampling_time, y_samples[1,:], c='orange', label="Samples")
# ax4.plot(sampling_time, yhat[1,:], label="Estimated")

# for (t,pol) in pols:
#     time_range = np.arange(t-N+1, t, integration_dt)
#     pol_val = pol.deriv(1)(np.arange(0, N-1, integration_dt))
#     ax4.plot(time_range, pol_val, label=str(t-N+1))
#     ax4.legend()
# f4.tight_layout()

plt.show()
