import os
import tempfile
import unittest
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


if __name__ == '__main__':
    unittest.main()
