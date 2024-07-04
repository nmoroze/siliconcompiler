# Copyright 2020 Silicon Compiler Authors. All Rights Reserved.
import siliconcompiler
from siliconcompiler.scheduler import _setup_node

import os

import pytest

from tests.core.tools.fake import foo
from tests.core.tools.fake import bar
from tests.core.tools.fake import baz
from tests.core.tools.echo import echo

from siliconcompiler.tools.builtin import nop
from siliconcompiler.flowgraph import nodes_to_execute, _check_flowgraph


def test_check_manifest():
    chip = siliconcompiler.Chip('gcd')
    chip.load_target("freepdk45_demo")
    chip.input('examples/gcd/gcd.v')
    index = "0"
    steps = ['import', 'syn']
    for step in steps:
        _setup_node(chip, step, index)

    chip.set('option', 'to', ['syn'])

    chip.set('arg', 'step', None)
    chip.set('arg', 'index', None)
    assert chip.check_manifest()


@pytest.mark.eda
@pytest.mark.quick
def test_check_allowed_filepaths_pass(scroot, monkeypatch):
    chip = siliconcompiler.Chip('gcd')

    chip.input(os.path.join(scroot, 'examples', 'gcd', 'gcd.v'))
    chip.load_target("freepdk45_demo")

    flow = chip.get('option', 'flow')
    for step in chip.getkeys('flowgraph', flow):
        for index in chip.getkeys('flowgraph', flow, step):
            _setup_node(chip, step, index)

    # collect input files
    cwd = os.getcwd()
    workdir = chip.getworkdir(step='import', index='0')
    os.makedirs(workdir)
    os.chdir(workdir)
    chip.collect()
    os.chdir(cwd)

    assert chip.check_manifest()


@pytest.mark.eda
@pytest.mark.quick
def test_check_allowed_filepaths_fail(scroot, monkeypatch):
    chip = siliconcompiler.Chip('gcd')

    chip.input(os.path.join(scroot, 'examples', 'gcd', 'gcd.v'))
    chip.input('/random/abs/path/to/file.sdc')
    chip.set('input', 'constraint', 'sdc', False, field='copy')
    chip.load_target("freepdk45_demo")

    # collect input files
    workdir = chip.getworkdir(step='import', index='0')
    cwd = os.getcwd()
    os.makedirs(workdir)
    os.chdir(workdir)
    chip.collect()
    os.chdir(cwd)

    assert not chip.check_manifest()


def test_check_missing_file_param():
    chip = siliconcompiler.Chip('gcd')
    chip.load_target("freepdk45_demo")

    _setup_node(chip, 'syn', '0')

    chip.set('arg', 'step', 'syn')
    chip.set('arg', 'index', '0')

    chip.set('tool', 'yosys', 'task', 'syn_asic', 'input', [], step='syn', index='0')
    chip.set('tool', 'yosys', 'task', 'syn_asic', 'output', [], step='syn', index='0')

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
    chip.node(flow, 'import', nop)
    chip.node(flow, 'parallel1', foo)
    chip.node(flow, 'parallel2', bar)
    chip.edge(flow, 'import', 'parallel1')
    chip.edge(flow, 'import', 'parallel2')

    chip.node(flow, 'export', baz)
    chip.edge(flow, 'parallel1', 'export')
    chip.edge(flow, 'parallel2', 'export')
    chip.set('option', 'flow', flow)

    chip.set('tool', 'foo', 'exe', 'foo')
    chip.set('tool', 'bar', 'exe', 'foo')
    chip.set('tool', 'baz', 'exe', 'baz')

    chip.set('tool', 'fake', 'task', 'baz', 'input', ['foo.out', 'bar.out'],
             step='export', index='0')

    return chip


def test_merged_graph_good(merge_flow_chip):
    merge_flow_chip.set('tool', 'fake', 'task', 'foo', 'output', 'bar.out',
                        step='parallel1', index='0')
    merge_flow_chip.set('tool', 'fake', 'task', 'bar', 'output', 'foo.out',
                        step='parallel2', index='0')

    assert merge_flow_chip.check_manifest()


def test_merged_graph_good_from_to():
    chip = siliconcompiler.Chip('test')
    flow = 'test'
    chip.node(flow, 'import', nop)
    chip.node(flow, 'parallel1', echo)
    chip.node(flow, 'parallel2', echo)
    chip.node(flow, 'merge', echo)
    chip.node(flow, 'export', echo)
    chip.edge(flow, 'import', 'parallel1')
    chip.edge(flow, 'import', 'parallel2')
    chip.edge(flow, 'parallel1', 'merge')
    chip.edge(flow, 'parallel2', 'merge')
    chip.edge(flow, 'merge', 'export')
    chip.set('option', 'flow', flow)
    chip.set('option', 'mode', 'asic')

    chip.run()

    chip.set('option', 'from', ['merge'])
    chip.set('option', 'to', ['export'])

    assert chip.check_manifest()


def test_merged_graph_bad_same(merge_flow_chip):
    # Two merged steps can't output the same thing
    merge_flow_chip.set('tool', 'fake', 'task', 'foo', 'output', 'foo.out',
                        step='parallel1', index='0')
    merge_flow_chip.set('tool', 'fake', 'task', 'bar', 'output', 'foo.out',
                        step='parallel2', index='0')

    assert not merge_flow_chip.check_manifest()


def test_merged_graph_bad_missing(merge_flow_chip):
    # bar doesn't provide necessary output
    merge_flow_chip.set('tool', 'fake', 'task', 'foo', 'output', 'foo.out',
                        step='parallel1', index='0')

    assert not merge_flow_chip.check_manifest()


def test_check_missing_task_module():
    chip = siliconcompiler.Chip('gcd')

    chip.load_target("freepdk45_demo")

    chip.set('flowgraph', chip.get('option', 'flow'), 'place', '0', 'taskmodule', 'missing.place')

    assert not chip.check_manifest()


def test_check_graph_duplicate_edge():
    chip = siliconcompiler.Chip('test')

    flow = 'test'
    chip.set('option', 'flow', flow)

    chip.node(flow, 'import', foo)
    chip.node(flow, 'export', baz)

    chip.edge(flow, 'import', 'export')

    # edge() should not allow duplicates
    chip.edge(flow, 'import', 'export')
    assert len(chip.get('flowgraph', flow, 'export', '0', 'input')) == 1

    # check_manifest() should catch it if forced
    chip.add('flowgraph', flow, 'export', '0', 'input', ('import', '0'))

    assert not _check_flowgraph(chip)


def test_check_missing_library():
    chip = siliconcompiler.Chip('test')
    chip.load_target("gf180_demo")

    chip.add('option', 'library', 'sc_test')

    for step, index in nodes_to_execute(chip, chip.get('option', 'flow')):
        # Setting up tool is optional
        _setup_node(chip, step, index)

    assert not chip.check_manifest()


#########################
if __name__ == "__main__":
    test_check_manifest()
    test_check_missing_file_param()
