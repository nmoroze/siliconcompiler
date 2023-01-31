import os
import copy
import siliconcompiler

def make_docs():
    '''
    Nangate open standard cell library for FreePDK45.
    '''
    chip = siliconcompiler.Chip('<design>')
    setup(chip)
    return chip

def setup(chip):
    libname = 'nangate45'
    foundry = 'virtual'
    process = 'freepdk45'
    stackup = '10M'
    libtype = '10t'
    version = 'r1p0'
    corner = 'typical'
    objectives = ['setup']

    libdir = os.path.join('..',
                          'third_party',
                          'pdks',
                          foundry,
                          process,
                          'libs',
                          libname,
                          version)


    # create local chip object
    lib = siliconcompiler.Chip(libname)

    # version
    lib.set('package', 'version', version)

    # list of stackups supported
    lib.set('option', 'stackup', stackup)

    # list of pdks supported
    lib.set('option', 'pdk', process)

    # footprint/type/sites
    lib.set('asic', 'libarch', libtype)
    lib.set('asic', 'site', libtype, 'FreePDK45_38x28_10R_NP_162NW_34O')

    # timing
    lib.add('output', corner, 'nldm',
             libdir+'/lib/NangateOpenCellLibrary_typical.lib')

    # lef
    lib.add('output', stackup, 'lef',
             libdir+'/lef/NangateOpenCellLibrary.macro.mod.lef')

    # gds
    lib.add('output', stackup, 'gds',
             libdir+'/gds/NangateOpenCellLibrary.gds')

    # cdl
    lib.add('output', stackup, 'cdl',
             libdir+'/cdl/NangateOpenCellLibrary.cdl')

    # clock buffers
    lib.add('asic', 'cells','clkbuf', "BUF_X4")

    # tie cells
    lib.add('asic', 'cells','tie', ["LOGIC1_X1",
                                    "LOGIC0_X1"])

    # hold cells
    lib.add('asic', 'cells', 'hold', "BUF_X1")

    # filler
    lib.add('asic', 'cells', 'filler', ["FILLCELL_X1",
                                        "FILLCELL_X2",
                                        "FILLCELL_X4",
                                        "FILLCELL_X8",
                                        "FILLCELL_X16",
                                        "FILLCELL_X32"])

    # Stupid small cells
    lib.add('asic', 'cells', 'dontuse', ["AOI211_X1",
                                         "OAI211_X1"])

    # Tapcell
    lib.add('asic', 'cells','tap', "FILLCELL_X1")

    # Endcap
    lib.add('asic', 'cells','endcap', "FILLCELL_X1")

    # Techmap
    lib.add('option', 'file', 'yosys_techmap', libdir + '/techmap/yosys/cells_latch.v')

    # Defaults for OpenROAD tool variables
    lib.set('option', 'var', 'openroad_place_density', '0.35')
    lib.set('option', 'var', 'openroad_pad_global_place', '2')
    lib.set('option', 'var', 'openroad_pad_detail_place', '1')
    lib.set('option', 'var', 'openroad_macro_place_halo', ['22.4', '15.12'])
    lib.set('option', 'var', 'openroad_macro_place_channel', ['18.8', '19.95'])

    lib.set('option', 'file', 'openroad_tapcells', libdir + '/apr/openroad/tapcell.tcl')
    lib.set('option', 'file', 'openroad_pdngen', libdir + '/apr/openroad/pdngen.tcl')
    lib.set('option', 'file', 'openroad_global_connect', libdir + '/apr/openroad/global_connect.tcl')

    lib.set('option', 'var', 'yosys_driver_cell', "BUF_X4")
    lib.set('option', 'var', 'yosys_buffer_cell', "BUF_X1")
    lib.set('option', 'var', 'yosys_buffer_input', "A")
    lib.set('option', 'var', 'yosys_buffer_output', "Z")
    for tool in ('yosys', 'openroad'):
        lib.set('option', 'var', f'{tool}_tiehigh_cell', "LOGIC1_X1")
        lib.set('option', 'var', f'{tool}_tiehigh_port', "Z")
        lib.set('option', 'var', f'{tool}_tielow_cell', "LOGIC0_X1")
        lib.set('option', 'var', f'{tool}_tielow_port', "Z")

    chip.import_library(lib)

#########################
if __name__ == "__main__":

    lib = make_docs()
    lib.write_manifest('nangate45.tcl')
