import os
import siliconcompiler

def test_check_logfile(datadir):

    chip = siliconcompiler.Chip('gcd')
    chip.load_target('freepdk45_demo')

    # add regex
    chip.add('tool', 'openroad', 'task', 'place', 'regex', 'place', '0', 'warnings', "WARNING")
    chip.add('tool', 'openroad', 'task', 'place', 'regex', 'place', '0', 'warnings', "-v DPL")

    # check log
    logfile = os.path.join(datadir, 'place.log')
    chip.check_logfile(step='place', logfile=logfile)


#########################
if __name__ == "__main__":
    from tests.fixtures import datadir
    test_check_logfile(datadir(__file__))
