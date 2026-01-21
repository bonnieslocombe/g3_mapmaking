# ============================================================================ #
# g3mapmaker.py
#
# Bonnie Slocombe
#
# G3 pipeline module for map-making
# ============================================================================ #

from spt3g import core
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
import h5py, io

class QuickMapMaker(core.G3Module):
    """
    Bins multi-detector TOD into a 2D sky map, correcting for detector offsets.
    """

    def __init__(self, 
                 ra0, 
                 dec0, 
                 xlen=1.0, 
                 ylen=1.0, 
                 res=0.01):
        """
        Create a new MapMaker.

        :param ra0: G3Units angle - center of map in right ascension
        :param dec0: G3Units angle - center of map in declination
        :param xlen: G3Units angle - width of map in right ascension
        :param ylen: G3Units angle - height of map in declination
        :param res: G3Units angle - size of map square pixels
        """
        
        super().__init__()
        self.ra0 = ra0
        self.dec0 = dec0
        self.xlen = xlen
        self.ylen = ylen
        self.res = res

        # Map grid (number of bins along each axis)
        self.nx = int(xlen / res)
        self.ny = int(ylen / res)
        self.ra_edges = np.linspace(-xlen/2, xlen/2, self.nx+1) + ra0
        self.dec_edges = np.linspace(-ylen/2, ylen/2, self.ny+1) + dec0
        self.sky_map = np.zeros((self.ny, self.nx), dtype=float)
        self.hits_map = np.zeros((self.ny, self.nx), dtype=int)

        # Detector offsets
        self.det_offset_dict = {}


    def Process(self, frame):
        """
        Access data frames to get detector offsets, signal, and RA/Dec.
        """
        
        if frame.type == core.G3FrameType.Calibration:
            # Load detector offsets
            fp_buffer = io.BytesIO(bytes(frame["focalplane"]))
            with h5py.File(fp_buffer, "r") as f:
                names = [n.decode("utf-8") for n in f["focalplane"]["name"][:]]
                quats = f["focalplane"]["quat"][:]
                self.det_offset_dict = {name: quat for name, quat in zip(names, quats)}
            return frame

        if frame.type == core.G3FrameType.Scan:
            raw_signal = frame["signal"]
            kids = list(raw_signal.keys())

            # Boresight quaternions
            boresight_q = np.asarray(frame["shared_boresight_radec"])  # Format is scalar-first
            
            # Create rotation object from quaterion -- Note: quaternion is converted to vector-first format for this function
            boresight_r = R.from_quat(boresight_q[:, [1,2,3,0]])
            
            # Create unit vector to apply final rotation to
            z_axis = np.array([0,0,1])
            
            # Loop over detectors
            for kid in kids:
                # Reconstruct signal
                y_raw = np.asarray(raw_signal[kid], float)
                gain_key = f"compress_signal_{kid}_gain"
                offset_key = f"compress_signal_{kid}_offset"
                if gain_key in frame and offset_key in frame:
                    gain = float(frame[gain_key])
                    offset = float(frame[offset_key])
                    y = y_raw/gain + offset
                else:
                    y = y_raw

                # Apply detector offsets
                det_q = self.det_offset_dict[kid] # quaternion for detector offset
                det_r = R.from_quat(det_q) # create rotation object: Note detector quaternions are already vector-first format
                corrected_r = boresight_r * det_r # Multiply rotation objects to apply detector offsets
                det_vectors = corrected_r.apply(z_axis) # apply final rotation to unit vector

                # Calculate RA/Dec for each detector
                ra_det = np.degrees(np.arctan2(det_vectors[:,1], det_vectors[:,0])) % 360
                dec_det = np.degrees(np.arcsin(det_vectors[:,2]))

                # Bin into sky map
                hist, _, _ = np.histogram2d(dec_det, ra_det,
                                            bins=[self.dec_edges, self.ra_edges],
                                            weights=y)
                self.sky_map += hist

                # Count hits per pixel
                hits, _, _ = np.histogram2d(dec_det, ra_det,
                                            bins=[self.dec_edges, self.ra_edges])
                self.hits_map += hits.astype(int)

            return frame

        
        if frame.type == core.G3FrameType.EndProcessing:

            print("Plotting final map...")

            # Avoid divide-by-zero
            hitmask = self.hits_map > 0
            final_map = np.zeros_like(self.sky_map)
            final_map[hitmask] = self.sky_map[hitmask]

            extent = [
                self.ra_edges[0], self.ra_edges[-1],
                self.dec_edges[0], self.dec_edges[-1]
            ]

            plt.figure(figsize=(7, 6))
            im = plt.imshow(
                final_map,
                origin="lower",
                extent=extent,
                aspect="auto"
            )
            plt.colorbar(im, label="Signal")
            plt.xlabel("RA [deg]")
            plt.ylabel("Dec [deg]")
            plt.title("Combined Sky Map")

            plt.tight_layout()
            plt.show()
            
            return frame


