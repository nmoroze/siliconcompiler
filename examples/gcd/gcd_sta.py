#!/usr/bin/env python3
# Copyright 2020 Silicon Compiler Authors. All Rights Reserved.

import os
import siliconcompiler
from siliconcompiler.targets import freepdk45_demo


def main():
    '''Simple asicflow example.'''
    root = os.path.dirname(__file__)

    chip = siliconcompiler.Chip('gcd')
    chip.input(os.path.join(root, "gcd.v"))
    chip.input(os.path.join(root, "gcd.sdc"))
    chip.set('option', 'quiet', True)
    chip.set('option', 'track', True)
    chip.set('option', 'hash', True)
    chip.set('option', 'nodisplay', True)
    chip.use(freepdk45_demo)
    chip.set('option', 'flow', 'synflow')
    chip.run()
    chip.summary()


if __name__ == '__main__':
    main()
