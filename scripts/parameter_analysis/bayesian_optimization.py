from bayes_opt import BayesianOptimization
import numpy as np

import matplotlib.pyplot as plt
from matplotlib import gridspec

# Install with 'sudo pip install bayesian-optimization'


# knownInputOutputs is dictionary of prior values e.g. { 'target': [...], 'x': [...]}
# ranges is the range of each value e.g. {'x': (-2, 10)}
# acq can be 'ucb' (Upper Confidence Bound) or 'ei' (Expected Improvement)
# kappa is exploration vs exploitation. 10 -> much exploration, 1 -> extreme exploitation
def BayesianOptimizeArgmax(priorInputs, priorOutputs, ranges, acq='ucb', kappa=5):
    bo = BayesianOptimization(None, ranges)

    inputsOutputs = priorInputs.copy()
    inputsOutputs.update(priorOutputs)
    bo.initialize(inputsOutputs)

    bo.maximize(init_points=0, n_iter=0, acq=acq, kappa=kappa)

    # Argmax
    x = np.linspace(-2, 10, 1000).reshape(-1, 1)
    y = np.linspace(-2, 10, 1000).reshape(-1, 1)

    utility = bo.util.utility(np.hstack((x, y)), bo.gp, 0)
    print utility
    return x[np.argmax(utility)], y[np.argmax(utility)]
    pass


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

    ranges = {'x': (-2, 10), 'y': (-2,10)}
    testIn = {'x': [-2, 2.6812, 1.6509, 10], 'y': [-2, 2.6812, 1.6509, 10]}
    testOut = {'target': [0.20166, 1.08328, 1.30455, 0.21180]}
    print BayesianOptimizeArgmax(testIn, testOut, ranges)

    if False:
        def target(x):
            return np.exp(-(x - 2)**2) + np.exp(-(x - 6)**2 / 10) + 1 / (x**2 + 1)


        x = np.linspace(-2, 10, 10000).reshape(-1, 1)
        y = target(x)

        bo = BayesianOptimization(target, {'x': (-2, 10)})

        # Additionally, if we have any prior knowledge of the behaviour of
        # the target function (even if not totally accurate) we can also
        # tell that to the optimizer.
        # Here we pass a dictionary with 'target' and parameter names as keys and a
        # list of corresponding values
        bo.initialize({
            'target': [0.20166, 1.08328, 1.30455, 0.21180],
            'x': [-2, 2.6812, 1.6509, 10]
        })

        # utility = Upper Confidence Bound
        # alternative acq = 'ei' (Expected Improvement)
        # kappa = exploration vs exploitation. 10 -> much exploration, 1 -> only tight exploitation
        bo.maximize(init_points=5, n_iter=5, acq='ucb', kappa=5)

        # The output values can be accessed with self.res
        print 'Best param/output so far:', bo.res['max']

        utility = bo.util.utility(x, bo.gp, 0)
        print 'Best param to test next:', x[np.argmax(utility)]

        # # Making changes to the gaussian process can impact the algorithm
        # # dramatically.
        # gp_params = {'kernel': None, 'alpha': 1e-5}

        # # Run it again with different acquisition function
        # bo.maximize(n_iter=5, acq='ei', **gp_params)



        plot_gp(bo, x, y)