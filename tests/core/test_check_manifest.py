# Copyright 2020 Silicon Compiler Authors. All Rights Reserved.
import siliconcompiler

import os

import pytest

def test_check_manifest():

    chip = siliconcompiler.Chip('gcd')
    chip.load_target("freepdk45_demo")
    chip.set('input', 'rtl', 'verilog', 'examples/gcd/gcd.v')
    flow = chip.get('option', 'flow')
    index = "0"
    steps = ['import', 'syn']
    for step in steps:
        tool = chip.get('flowgraph', flow, step, index, 'tool')
        chip.set('arg', 'step', step)
        chip.set('arg', 'index', index)
        setup = chip.find_function(tool, 'setup', 'tools')
        assert setup is not None
        setup(chip)

    chip.set('option', 'steplist', steps)

    chip.set('arg', 'step', None)
    chip.set('arg', 'index', None)
    assert chip.check_manifest()

@pytest.mark.eda
@pytest.mark.quick
def test_check_allowed_filepaths_pass(scroot, monkeypatch):
    chip = siliconcompiler.Chip('gcd')

    chip.set('input', 'rtl', 'verilog', os.path.join(scroot, 'examples', 'gcd', 'gcd.v'))
    chip.load_target("freepdk45_demo")

    # collect input files
    cwd = os.getcwd()
    workdir = chip._getworkdir(step='import', index='0')
    os.makedirs(workdir)
    os.chdir(workdir)
    chip._collect('import', '0')
    os.chdir(cwd)

    env = {
        'SC_VALID_PATHS': os.path.join(scroot, 'third_party', 'pdks'),
        'SCPATH': os.environ['SCPATH']
    }
    monkeypatch.setattr(os, 'environ', env)

    assert chip.check_manifest()

@pytest.mark.eda
@pytest.mark.quick
def test_check_allowed_filepaths_fail(scroot, monkeypatch):
    chip = siliconcompiler.Chip('gcd')

    chip.set('input', 'rtl', 'verilog', os.path.join(scroot, 'examples', 'gcd', 'gcd.v'))
    chip.set('input', 'constraint', 'sdc', '/random/abs/path/to/file.sdc')
    chip.set('input', 'constraint', 'sdc', False, field='copy')
    chip.load_target("freepdk45_demo")

    # collect input files
    workdir = chip._getworkdir(step='import', index='0')
    cwd = os.getcwd()
    os.makedirs(workdir)
    os.chdir(workdir)
    chip._collect('import', '0')
    os.chdir(cwd)

    env = {
        'SC_VALID_PATHS': os.path.join(scroot, 'third_party', 'pdks'),
        'SCPATH': os.environ['SCPATH']
    }
    monkeypatch.setattr(os, 'environ', env)

    assert not chip.check_manifest()

def test_check_missing_file_param():
    chip = siliconcompiler.Chip('gcd')
    chip.load_target("freepdk45_demo")

    chip._setup_tool('yosys', 'syn', 'syn', '0')

    chip.set('arg', 'step', 'syn')
    chip.set('arg', 'index', '0')

    chip.set('tool', 'yosys', 'task', 'syn', 'input', 'syn', '0', [])
    chip.set('tool', 'yosys', 'task', 'syn', 'output', 'syn', '0',[])

    # not real file, will cause error
    libname = 'nangate45'
    corner = 'typical'
    chip.add('library', libname, 'output', corner, 'nldm',
             '/fake/timing/file.lib')

    assert not chip.check_manifest()

@pytest.fixture
def merge_flow_chip():
    chip = siliconcompiler.Chip('test')

    flow = 'test'
    chip.node(flow, 'import', 'nop', 'nop')
    chip.node(flow, 'parallel1', 'foo', 'parallel1')
    chip.node(flow, 'parallel2', 'bar', 'parallel2')
    chip.edge(flow, 'import', 'parallel1')
    chip.edge(flow, 'import', 'parallel2')

    chip.node(flow, 'export', 'baz', 'export')
    chip.edge(flow, 'parallel1', 'export')
    chip.edge(flow, 'parallel2', 'export')
    chip.set('option', 'flow', flow)

    chip.set('tool', 'foo', 'exe', 'foo')
    chip.set('tool', 'bar', 'exe', 'foo')
    chip.set('tool', 'baz', 'exe', 'baz')

    chip.set('tool', 'baz', 'task', 'export', 'input', 'export', '0', ['foo.out', 'bar.out'])

    return chip

def test_merged_graph_good(merge_flow_chip):
    merge_flow_chip.set('tool', 'foo', 'task', 'parallel1', 'output', 'parallel1', '0', 'bar.out')
    merge_flow_chip.set('tool', 'bar', 'task', 'parallel2', 'output', 'parallel2', '0', 'foo.out')

    assert merge_flow_chip.check_manifest()

def test_merged_graph_good_steplist():
    chip = siliconcompiler.Chip('test')
    flow = 'test'
    chip.node(flow, 'import', 'nop', 'nop')
    chip.node(flow, 'parallel1', 'echo', 'parallel1')
    chip.node(flow, 'parallel2', 'echo', 'parallel2')
    chip.node(flow, 'merge', 'echo', 'merge')
    chip.node(flow, 'export', 'echo', 'export')
    chip.edge(flow, 'import', 'parallel1')
    chip.edge(flow, 'import', 'parallel2')
    chip.edge(flow, 'parallel1', 'merge')
    chip.edge(flow, 'parallel2', 'merge')
    chip.edge(flow, 'merge', 'export')
    chip.set('option', 'flow', flow)
    chip.set('flowgraph', flow, 'import', '0', 'task', 'echo')
    chip.set('flowgraph', flow, 'merge', '0', 'task', 'echo')
    chip.set('flowgraph', flow, 'export', '0', 'task', 'echo')
    chip.set('flowgraph', flow, 'parallel1', '0', 'task', 'echo')
    chip.set('flowgraph', flow, 'parallel2', '0', 'task', 'echo')

    chip.run()

    chip.set('option', 'steplist', ['merge', 'export'])

    assert chip.check_manifest()

def test_merged_graph_bad_same(merge_flow_chip):
    # Two merged steps can't output the same thing
    merge_flow_chip.set('tool', 'foo', 'task', 'parallel1', 'output', 'parallel1', '0', 'foo.out')
    merge_flow_chip.set('tool', 'bar', 'task', 'parallel2', 'output', 'parallel2', '0', 'foo.out')

    assert not merge_flow_chip.check_manifest()

def test_merged_graph_bad_missing(merge_flow_chip):
    # bar doesn't provide necessary output
    merge_flow_chip.set('tool', 'foo', 'task', 'parallel1', 'output', 'parallel1', '0', 'foo.out')

    assert not merge_flow_chip.check_manifest()

#########################
if __name__ == "__main__":
    test_check_manifest()
    test_check_missing_file_param()
