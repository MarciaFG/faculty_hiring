#!/usr/bin/env python

__author__ = "Sam Way"
__copyright__ = "Copyright 2014, The Clauset Lab"
__license__ = "BSD"
__maintainer__ = "Sam Way"
__email__ = "samfway@gmail.com"
__status__ = "Development"


import argparse
import numpy as np
import cProfile
from scipy.optimize import minimize
from faculty_hiring.parse.load import load_assistant_prof_pools
from faculty_hiring.parse.institution_parser import parse_institution_records
from faculty_hiring.models.simulation_engine import SimulationEngine
from faculty_hiring.models.null_models import ConfigurationModel, BestFirstModel
from faculty_hiring.models.sigmoid_models import SigmoidModel


def interface():
    args = argparse.ArgumentParser()
    args.add_argument('-f', '--fac-file', help='Faculty file', required=True)
    args.add_argument('-i', '--inst-file', help='Institutions file', required=True)
    args.add_argument('-p', '--prob-function', help='Candidate probability/matching function', required=True)
    args.add_argument('-n', '--num-iters', help='Number of iterations to est. error', default=150, type=int)
    args.add_argument('-s', '--num-steps', help='Number of steps allowed', default=100, type=int)
    args.add_argument('-r', '--reg', help='Regularization amount', default=1e-10, type=float)
    args.add_argument('-v', '--validation', help='Years to hold out', default='')
    args = args.parse_args()
    return args


if __name__=="__main__":
    args = interface()
    
    inst = parse_institution_records(open(args.inst_file, 'rU'))
    candidate_pools, job_pools, job_ranks, year_range = load_assistant_prof_pools(open(args.fac_file), 
                                                                                  school_info=inst, 
                                                                                  ranking='pi_rescaled',
                                                                                  year_start=1970, 
                                                                                  year_stop=2012, 
                                                                                  year_step=1)

    if args.validation:  # if specified years are to be left out
        hold_out = [int(year) for year in args.validation.split(',')]
        training_candidates, training_jobs, training_job_ranks = [], [], []
        for i, year in enumerate(year_range):
            if year not in hold_out:
                training_candidates.append(candidate_pools[i])
                training_jobs.append(job_pools[i])
                training_job_ranks.append(job_ranks[i])
        # Overwrite originals 
        candidate_pools, job_pools, job_ranks = training_candidates, training_jobs, training_job_ranks
    
    model = SigmoidModel(prob_function=args.prob_function)

    # Find a decent starting place
    simulator = SimulationEngine(candidate_pools, job_pools, job_ranks, inst, model, power=1, reg=args.reg, iters=20)
    w0 = None
    best_error = np.inf
    for i in xrange(args.num_steps):
        wtemp = 200*(np.random.random(model.num_weights()) - 0.5)  # ~[-100, 100]
        error = simulator.simulate(weights=wtemp)
        if error < best_error:
            w0 = wtemp.copy()
            best_error = error

    # Optimize from there
    simulator = SimulationEngine(candidate_pools, job_pools, job_ranks, inst, model, power=1, reg=args.reg, iters=args.num_iters)
    opt = {'maxiter':args.num_steps}
    res = minimize(simulator.simulate, w0, method='Nelder-Mead', options=opt)
    print res

