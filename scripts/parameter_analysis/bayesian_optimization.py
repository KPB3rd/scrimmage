from bayes_opt import BayesianOptimization
import numpy as np

import matplotlib.pyplot as plt
from matplotlib import gridspec

# Install with 'sudo pip install bayesian-optimization'



def posterior(bo, x, xmin=-2, xmax=10):
    xmin, xmax = -2, 10
    bo.gp.fit(bo.X, bo.Y)
    mu, sigma = bo.gp.predict(x, return_std=True)
    return mu, sigma


def plot_gp(bo, x, y):

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(
        'Gaussian Process and Utility Function After {} Steps'.format(
            len(bo.X)),
        fontdict={'size': 30})

    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
    axis = plt.subplot(gs[0])
    acq = plt.subplot(gs[1])

    mu, sigma = posterior(bo, x)
    axis.plot(x, y, linewidth=3, label='Target')
    axis.plot(
        bo.X.flatten(),
        bo.Y,
        'D',
        markersize=8,
        label=u'Observations',
        color='r')
    axis.plot(x, mu, '--', color='k', label='Prediction')

    axis.fill(
        np.concatenate([x, x[::-1]]),
        np.concatenate([mu - 1.9600 * sigma, (mu + 1.9600 * sigma)[::-1]]),
        alpha=.6,
        fc='c',
        ec='None',
        label='95% confidence interval')

    axis.set_xlim((-2, 10))
    axis.set_ylim((None, None))
    axis.set_ylabel('f(x)', fontdict={'size': 20})
    axis.set_xlabel('x', fontdict={'size': 20})

    utility = bo.util.utility(x, bo.gp, 0)
    acq.plot(x, utility, label='Utility Function', color='purple')
    acq.plot(
        x[np.argmax(utility)],
        np.max(utility),
        '*',
        markersize=15,
        label=u'Next Best Guess',
        markerfacecolor='gold',
        markeredgecolor='k',
        markeredgewidth=1)
    acq.set_xlim((-2, 10))
    acq.set_ylim((0, np.max(utility) + 0.5))
    acq.set_ylabel('Utility', fontdict={'size': 20})
    acq.set_xlabel('x', fontdict={'size': 20})

    axis.legend(loc=2, bbox_to_anchor=(1.01, 1), borderaxespad=0.)
    acq.legend(loc=2, bbox_to_anchor=(1.01, 1), borderaxespad=0.)
    plt.show()



if __name__ == '__main__':
    def target(x):
        return np.exp(-(x - 2)**2) + np.exp(-(x - 6)**2 / 10) + 1 / (x**2 + 1)


    x = np.linspace(-2, 10, 10000).reshape(-1, 1)

    bo = BayesianOptimization(target, {'x': (-2, 10)})

    # Additionally, if we have any prior knowledge of the behaviour of
    # the target function (even if not totally accurate) we can also
    # tell that to the optimizer.
    # Here we pass a dictionary with 'target' and parameter names as keys and a
    # list of corresponding values
    # bo.initialize(
    #     {
    #         'target': [-1, -1],
    #         'x': [1, 1],
    #         'y': [0, 2]
    #     }
    # )

    # utility = Upper Confidence Bound
    # kappa = exploration vs exploitation. 10 -> much exploration, 1 -> only tight exploitation
    bo.maximize(init_points=2, n_iter=5, acq='ucb', kappa=5)

    # The output values can be accessed with self.res
    print 'Best param/output so far:', bo.res['max']

    utility = bo.util.utility(x, bo.gp, 0)
    print 'Best param to test next:', x[np.argmax(utility)]

    plot_gp(bo, x, y)
