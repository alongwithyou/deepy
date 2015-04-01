#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging as loggers

import theano
import theano.tensor as T

from deepy.util.functions import FLOATX
from deepy.trainers.util import wrap_core


logging = loggers.getLogger(__name__)

def optimize_updates(params, gradients, config=None, shapes=None):
    """
    General optimization function for Theano.
    Parameters:
        params - parameters
        gradients - gradients
        config - training config
    Returns:
        Theano updates
    :type config: deepy.TrainerConfig
    """
    # Clipping
    if config:
        max_norm = config.get("max_norm", 5.0)
        clip = config.get("clip", True)

        if max_norm and clip:
            clipped_gradients = []
            norm_constant = T.constant(max_norm, dtype=FLOATX)
            for g in gradients:
                grad_norm = g.norm(L=2)
                g = (T.minimum(norm_constant, grad_norm)/ grad_norm) * g
                clipped_gradients.append(g)
            gradients = clipped_gradients
    # Find method
    method = "SGD"
    if config:
        method = config.get("method", method).upper()
    # Get Function
    func = None
    if method in ["SGD", "ADAGRAD", "ADADELTA", "FINETUNING_ADAGRAD"]:
        from ada_family import ada_family_core
        func = ada_family_core
    elif method == "ADAM":
        from adam import adam_core
        func = adam_core
    elif method == "RMSPROP":
        from rmsprop import rmsprop_core
        func = rmsprop_core
    elif method == "MOMENTUM":
        from momentum import momentum_core
        func = momentum_core

    if not func:
        raise NotImplementedError("method '%s' is not supported" % method)

    logging.info("optimize method=%s parameters=%s" % (method, str(params)))

    return wrap_core(func, config, params, gradients)

def optimize_function(params, config=None):
    """
    Create a optimizing function receives gradients.
    Parameters:
        params - parameters
        config - training configuration
    Returns:
        updating function receives gradients
    """
    gs = [T.matrix() if p.ndim == 2 else T.vector() for p in params]
    updates = optimize_updates(params, gs, config)
    return theano.function(gs, [], updates=updates)