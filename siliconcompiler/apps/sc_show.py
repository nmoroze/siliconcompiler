# Copyright 2020 Silicon Compiler Authors. All Rights Reserved.
import sys
import os
import siliconcompiler
from siliconcompiler._metadata import default_iomap

def main():
    progname = "sc-show"
    description = """
    --------------------------------------------------------------
    Restricted SC app that displays the layout of a design
    based on a file provided or tries to display the final
    layout based on loading the json manifest from:
    build/<design>/job0/<design>.pkg.json

    Examples:

    sc-show -design adder
    (displays build/job0/adder/export/0/outputs/adder.gds)

    sc-show build/job0/adder/route/1/outputs/adder.def
    (displays build/job0/adder/route/1/outputs/adder.def)

    """


    # TODO: this is a hack to get around design name requirement: since legal
    # design names probably can't contain spaces, we can detect if it is unset.
    UNSET_DESIGN = '  unset  '

    # Create a base chip class.
    chip = siliconcompiler.Chip(UNSET_DESIGN)

    # Fill input map with default mapping only for showable files
    input_map = {}
    for ext in ('gds', 'def'):
        if ext in default_iomap:
            input_map[ext] = default_iomap[ext]

    chip.create_cmdline(progname,
                        switchlist=['-design', '-input', '-loglevel', '-cfg'],
                        description=description,
                        input_map=input_map)

    #Error checking
    design = chip.get('design')
    design_set = design != UNSET_DESIGN
    gds_mode = chip.valid('input', 'layout', 'gds') and bool(chip.get('input', 'layout', 'gds'))
    def_mode = chip.valid('input', 'layout', 'def') and bool(chip.get('input', 'layout', 'def'))

    if def_mode and gds_mode:
        chip.logger.error('Exclusive options -input_gds and -input_def cannot both be defined.')
        sys.exit(1)
    if not (design_set or def_mode or gds_mode):
        chip.logger.error('Nothing to load: please define a target with -cfg, -design, -input_def, and/or -input_gds.')
        sys.exit(1)

    filename = None
    if gds_mode:
        filename = chip.get('input', 'layout', 'gds')[-1]
    elif def_mode:
        filename = chip.get('input', 'layout', 'def')[-1]

    if (filename is not None) and (not chip.get('option', 'cfg')):
        # only autoload manifest if user doesn't supply manually
        design = os.path.splitext(os.path.basename(filename))[0]
        dirname = os.path.dirname(filename)
        manifest = os.path.join(*[dirname, design+'.pkg.json'])
        if not os.path.isfile(manifest):
            chip.logger.error(f'Unable to automatically find manifest for design {design}. '
                'Please provide a manifest explicitly using -cfg.')
            sys.exit(1)
        chip.read_manifest(manifest)
    elif not chip.get('option', 'cfg'):
        # TODO: should we consider using showable?
        manifest = os.path.join(chip._getworkdir(), f'{design}.pkg.json')
        if not os.path.isfile(manifest):
            chip.logger.warning('Could not find manifest from design name')
        else:
            chip.read_manifest(manifest)

        filename = chip.find_result('gds', step='export')
        if filename is None:
            chip.logger.error('No final GDS export found for design')
            sys.exit(1)

    # Read in file
    chip.logger.info(f"Displaying {filename}")

    success = chip.show(filename)

    return 0 if success else 1

#########################
if __name__ == "__main__":
    sys.exit(main())
