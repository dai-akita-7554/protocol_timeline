import os
import sys
import tempfile
import unittest
import subprocess
import xml.etree.ElementTree as ET
from graphviz import Source
from timeline import Procedure, Timeline, from_md

class TestRelativeTime(unittest.TestCase):
    def from_text(self, text):
        with tempfile.TemporaryDirectory() as dirname:
            mdfile = os.path.join(dirname, 'input.md')
            with open(mdfile, 'w', encoding='utf8') as f:
                f.write(text)
            return from_md(mdfile)

    def test_unknown_relative_reference(self):
        text = '''<!--- body --->
## *P1* Step 1 _09:00~_
## *P2* Step 2 _MISSING+0:10~_ <!-- P1 -->
'''
        with self.assertRaisesRegex(ValueError, 'P2.*MISSING'):
            self.from_text(text)

    def test_unknown_relative_reference_in_empty_timeline(self):
        tl = Timeline()
        proc = Procedure(id = 'P1', start = 'MISSING+0:10')

        with self.assertRaisesRegex(ValueError, 'P1.*MISSING'):
            tl.append(proc)

        self.assertEqual(len(tl), 0)
        self.assertEqual(tl.t_max, 0)
        self.assertEqual(proc.wait, {})
        self.assertEqual(proc.start, 'MISSING+0:10')
        self.assertIsNone(proc.t)

    def test_unknown_relative_reference_preserves_timeline(self):
        tl = Timeline()
        first = Procedure(id = 'P1', start = '09:00')
        last = Procedure(id = 'P2', start = '09:05')
        tl.append(first)
        tl.append(last)
        proc = Procedure(id = 'P3', start = 'MISSING+0:10', prev = ['P1'])

        with self.assertRaisesRegex(ValueError, 'P3.*MISSING'):
            tl.append(proc)

        self.assertEqual(tl.procedures, [first, last])
        self.assertEqual(tl.t_max, 2)
        self.assertEqual(proc.wait, {})
        self.assertEqual(proc.start, 'MISSING+0:10')
        self.assertIsNone(proc.t)

    def test_relative_reference_to_earlier_procedure(self):
        text = '''<!--- body --->
## *P1* Step 1 _09:00~_
## *P2* Step 2 _09:05~_
## *P3* Step 3 _P1+0:10~_ <!-- P1 -->
'''
        tl = self.from_text(text)
        tl.compile()
        tl.render('test_relative_reference')

        self.assertEqual(len(tl), 3)
        self.assertEqual(tl[-1].wait, {'P1': '0:10'})
        self.assertEqual(tl[-1].prev, ['P1'])
        self.assertIsNone(tl[-1].start)
        self.assertEqual(tl[-1].t, 2)

    def test_relative_reference_with_end_time(self):
        tl = Timeline()
        tl.append(Procedure(id = 'P1', start = '09:00', end = '09:30'))
        proc = Procedure(id = 'P2', start = 'P1+0:10', prev = ['P1'])
        tl.append(proc)

        self.assertEqual(proc.wait, {'P1': '0:10'})
        self.assertEqual(proc.start, '09:40')
        self.assertEqual(proc.t, 1)


class TestPlaceOrder(unittest.TestCase):
    def test_places_follow_first_occurrence(self):
        tl = Timeline()
        for i, place in enumerate(['Beta', None, 'Alpha', 'Beta', None]):
            tl.append(Procedure(id = f'P{i}', label = f'Step {i}', place = place))
        tl.compile()
        tl.render('test_place_first_occurrence')
        source = tl.dot.source

        self.assertEqual(source.count('subgraph cluster_Beta'), 1)
        self.assertEqual(source.count('subgraph cluster_Alpha'), 1)
        self.assertNotIn('cluster_None', source)
        self.assertLess(source.index('subgraph cluster_Beta'), source.index('P1 ['))
        self.assertLess(source.index('P1 ['), source.index('subgraph cluster_Alpha'))
        self.assertLess(source.index('P4 ['), source.index('subgraph cluster_Alpha'))

    def test_place_order_is_stable_across_hash_seeds(self):
        text = '''<!--- body --->
## *P1* Step 1@Alpha _09:00~_
## *P2* Step 2@Beta _[P1]~_
'''
        script = '''import sys
from timeline import from_md

tl = from_md(sys.argv[1])
tl.compile()
sys.stdout.write(tl.dot.source)
'''
        directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        expected_source = None
        expected_order = None
        with tempfile.TemporaryDirectory() as dirname:
            mdfile = os.path.join(dirname, 'input.md')
            with open(mdfile, 'w', encoding='utf8') as f:
                f.write(text)
            for seed in ('0', '1', '2', '42'):
                with self.subTest(seed = seed):
                    env = os.environ.copy()
                    env['PYTHONHASHSEED'] = seed
                    result = subprocess.run(
                        [sys.executable, '-B', '-c', script, mdfile],
                        cwd = directory, env = env, check = True,
                        capture_output = True, encoding = 'utf8')
                    if expected_source is None:
                        expected_source = result.stdout
                    self.assertEqual(result.stdout, expected_source)

                    root = ET.fromstring(Source(result.stdout).pipe(format='svg'))
                    ns = {'s': 'http://www.w3.org/2000/svg'}
                    clusters = [
                        (float(g.find('s:text', ns).get('x')),
                         g.find('s:title', ns).text)
                        for g in root.findall('.//s:g[@class="cluster"]', ns)
                    ]
                    order = [name for x, name in sorted(clusters)]
                    self.assertEqual(set(order), {'cluster_Alpha', 'cluster_Beta'})
                    if expected_order is None:
                        expected_order = order
                    self.assertEqual(order, expected_order)

        Source(expected_source, format='pdf').render('test_place_order')


if __name__ == '__main__':
    unittest.main()
