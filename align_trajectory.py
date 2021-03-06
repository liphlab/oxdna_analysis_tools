#!/usr/bin/env python3

# align_trajectory.py
# Created by: Erik Poppleton
# Date: 8/26/19
# Takes a trajectory and aligns every frame to the first one and writes a new trajectory

try:
    from Bio.SVDSuperimposer import SVDSuperimposer
except:
    from bio.SVDSuperimposer import SVDSuperimposer
from sys import exit
from UTILS.readers import ErikReader
import numpy as np
import argparse
from compute_mean import normalize

#handle commandline arguments
parser = argparse.ArgumentParser(description="Aligns each frame in a trajectory to the first frame")
parser.add_argument('traj', type=str, nargs=1, help="The trajectory file to align")
parser.add_argument('outfile', type=str, nargs=1, help='The name of the new trajectory file to write out')
parser.add_argument('-i', metavar='index_file', dest='index_file', nargs=1, help='Align to only a subset of particles from a space-separated list in the provided file')
args = parser.parse_args()

#run system checks
from config import check_dependencies
check_dependencies(["python", "numpy", "Bio"])

#Parse command line arguments
traj_file = args.traj[0]
outfile = args.outfile[0]

#-i will make it only run on a subset of nucleotides.
#The index file is a space-separated list of particle IDs
if args.index_file:
    index_file = args.index_file[0]
    with open(index_file, 'r') as f:
        indexes = f.readline().split()
        try:
            indexes = [int(i) for i in indexes]
        except:
            print("ERROR: The index file must be a space-seperated list of particles.  These can be generated using oxView by clicking the \"Download Selected Base List\" button")
else: 
    with ErikReader(traj_file) as r:
        indexes = list(range(len(r.read().positions)))

#read the first configuration and use it as the reference configuration for the rest
r = ErikReader(traj_file)
ref = r.read()
ref.inbox()
ref_conf = ref.positions[indexes]
sup = SVDSuperimposer()

#The topology remains the same so we only write the configuration
ref.write_new(outfile)
mysystem = r.read()

#Read the trajectory one configuration at a time and perform the alignment
while mysystem != False:
    print("working on t = ", mysystem.time)
    #Need to get rid of fix_diffusion artifacts or SVD doesn't work
    mysystem.inbox()
    indexed_cur_conf = mysystem.positions[indexes]

    #Superimpose the configuration to the reference
    sup.set(ref_conf, indexed_cur_conf)
    sup.run()
    rot, tran = sup.get_rotran()

    #Apply rotation and translation in one step
    mysystem.positions = np.einsum('ij, ki -> kj', rot, mysystem.positions) + tran
    mysystem.a1s = np.einsum('ij, ki -> kj', rot, mysystem.a1s)
    mysystem.a3s = np.einsum('ij, ki -> kj', rot, mysystem.a3s)

    #print_lorenzo_output will create a new file, print_traj_output extends an existing file
    mysystem.write_append(outfile)

    mysystem = r.read()

