import parent_import # adds parent directory to sys.path

import signal
import sys

def signal_handler(sig, frame):
    print("WHAT")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

def cifar_experiment(model_name, clustered_input_chooser=False):
    import argparse

    parser = argparse.ArgumentParser(description=str(model_name) + ' experiment for testing CIFAR model.')
    # parser.add_argument("--lenet", type=int, default=1, choices=[1,4,5])
    parser.add_argument("--coverage", type=str, default="neuron", choices=["neuron", "kmn", "nbc", "snac"])
    parser.add_argument("--implicit_reward", type=bool, default=False)
    args = parser.parse_args()

    print("Arguments:", args)

    import numpy as np

    # CIFAR10 DATASET
    from keras.datasets import cifar10
    (train_images, train_labels), (test_images, test_labels) = cifar10.load_data()
    train_images = train_images.reshape(-1, 32, 32, 3).astype(np.int16)
    test_images = test_images.reshape(-1, 32, 32, 3).astype(np.int16)

    import os
    os.environ['KMP_DUPLICATE_LIB_OK']='True'

    from keras.models import load_model

    model = load_model("CIFAR10/cifar_original.h5")

    # COVERAGE
    if args.implicit_reward:
        def calc_implicit_reward_neuron(p1, p2):
            distance = np.abs(p1-p2)
            implicit_reward =  1 / (distance + 1)
            #print("p1, p2, distance, implicit_reward:", p1, p2, distance, implicit_reward)
            return implicit_reward

        def calc_implicit_reward(activation_values, covered_positions):
            #print("activation_values, covered_positions", activation_values, covered_positions)
            return np.max(activation_values * np.logical_not(covered_positions))
    else:
        calc_implicit_reward_neuron = None
        calc_implicit_reward = None

    if args.coverage == "neuron":
        from coverages.neuron_cov import NeuronCoverage
        coverage = NeuronCoverage(model, skip_layers=[0,5], calc_implicit_reward_neuron=calc_implicit_reward_neuron, calc_implicit_reward=calc_implicit_reward) # 0:input, 5:flatten
    elif args.coverage == "kmn" or args.coverage == "nbc" or args.coverage == "snac":
        from coverages.kmn import DeepGaugePercentCoverage
        k = 20
        coverage = DeepGaugePercentCoverage(model, k, train_images, skip_layers=[0,5], coverage_name=args.coverage, calc_implicit_reward_neuron=calc_implicit_reward_neuron, calc_implicit_reward=calc_implicit_reward) # 0:input, 5:flatten
    else:
        raise Exception("Unknown Coverage" + args.coverage)

    if clustered_input_chooser:
        from src.clustered_input_chooser import ClusteredInputChooser
        input_chooser = ClusteredInputChooser(test_images, test_labels)
    else:
        from src.input_chooser import InputChooser
        input_chooser = InputChooser(test_images, test_labels)

    return args, (train_images, train_labels), (test_images, test_labels), model, coverage, input_chooser