# g3_mapmaking
Initial progress on g3 pipeline for Quick-Look Mapmaking
## Overview
This work shows the initial stages of development for the CCAT Quick-Look Mapmaker. This is a continuation of the work by Jonah Lee https://github.com/jonahjlee/blasttng-to-g3.

Telescope and detector data for CCAT will be available in .g3 file format and packaged into a bound book for mapmaking. Since real data is not yet available, hdf5 files from a TOAST simulation of Jupiter were converted to .g3 files and used to test the initial pipeline. This simulation utilized 100 randomly selected detectors on the CCAT array and excluded noise. The objective was to use this simulation to explore the .g3 file format and become familiar with pipeline operations.

The `mapmaker` module contains the main script `g3mapmaker.py` used in the pipeline `full_g3pipeline.ipynb` to create a combined map of Jupiter from the simulated data files.

The notebook `Jupiter_sim.ipynb` explores the format of these .g3 files and explains how to apply detector offsets using quaternions.
