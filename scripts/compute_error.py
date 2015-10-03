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


def allow_negatives(x):
    return str(x)


def interface():
    args = argparse.ArgumentParser()
    args.add_argument('-f', '--fac-file', help='Faculty file', required=True)
    args.add_argument('-i', '--inst-file', help='Institutions file', required=True)
    args.add_argument('-p', '--prob-function', help='Candidate probability/matching function', required=True)
    args.add_argument('-n', '--num-iters', help='Number of iterations to est. error', default=100, type=int)
    args.add_argument('-w', '--weights', help='Model parameters (as comma-separated string)', type=allow_negatives)
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

    model = SigmoidModel(prob_function=args.prob_function)
    simulator = SimulationEngine(candidate_pools, job_pools, job_ranks, inst, model, iters=1, reg=0)
    if model.num_weights() > 0:
        w = np.array([float(x) for x in args.weights.split(',')])
        if len(w) != model.num_weights():
            print len(w), model.num_weights()
            raise ValueError('Invalid number of weights/model parameters!')
    else:
        w = None

    for i in xrange(args.num_iters):
        simulator.simulate(weights=w)

