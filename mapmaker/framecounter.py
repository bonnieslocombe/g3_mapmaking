# ============================================================================ #
# tools.py
#
# Jonah Lee
# https://github.com/jonahjlee/blasttng-to-g3.git
# ============================================================================ #

from spt3g import core
import numpy as np

class FrameCounter(core.G3Module):
    """
    G3 pipeline module

    Counts the frame types that pass through this module. Useful as a progress indicator since it updates live.
    Stacks and counts sequential frames of the same type.
    """
    def __init__(self):
        super(FrameCounter, self).__init__()
        self.previous_type = None
        self.num_repeats = 0
    def Process(self, frame):
        type = frame.type
        if type == self.previous_type:
            self.num_repeats += 1
            print(f"{type} (x{self.num_repeats + 1})", end='\r')
        else:
            print()
            print(f"{type}", end='\r')
            if type == core.G3FrameType.EndProcessing: print()
            self.num_repeats = 0
        self.previous_type = type
