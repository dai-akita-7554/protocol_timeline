Protocol timeline maker
==

Make a timeline graph from a formatted markdown file. This script generates a timeline graph as a pdf file `output.pdf` from the markdown file `input.md`.
```python
from timeline import from_md
tl = from_md('input.md')
tl.compile()
tl.render('output')
```


Format of protocol
==

A protocol is a list of procedures. A procedure is defined in the markdown file as follows:
```markdown
## *name* title@place _start~_ <!-- previous_procedures -->

text text text ...
```

- `*name*`: _necessary_ The unique name of the procedure to be referred in other procedures.
- `title`: _necessary_ The title of the procedure which is displayed in the timeline.
- `@place`: The place where the procedure should be done. The procedures are grouped by places in the timeline.
- `_start~_`: The starting time of the procedure. Other procedure can be referred. For example, given a procedure name `p`, 
  - `_[p]~_` means that the procedure starts at the same time with `p`
  - `_p+1:00~_` means that the procecure starts one hour after `p`
- `previous_procedures`: Comma-separated other procedures should be done before the procedure. These previous procedures are connected to the procedure by arrows in the timeline.

Relative starting times such as `_p+1:00~_` must refer to a previously listed procedure. If the reference is not found, `from_md()` or `Timeline.append()` raises a `ValueError` containing the procedure ID and the missing reference ID.

Place groups are added to the graph in their order of first appearance, making their output order independent of Python's hash seed. Graphviz determines their final left-to-right arrangement.

The program extract procedures written in the format after the line `<!--- body --->`.

The procedures are supposed to be listed in chronological order. Parallel procedures can be expressed by the starting time format. Date information can be added by inserting the dates in the format:
```markdown
# y/m/d
```


Tests
==

You can generate a timeline from the example in this README by running:
```sh
python test.py
```
This creates `readme.pdf` in the current directory.

To run the regression tests, execute the following command from the repository directory:
```sh
python -m unittest discover -s tests -v
```

The regression tests also generate `test_relative_reference.pdf`, `test_place_first_occurrence.pdf`, and `test_place_order.pdf` for visual inspection. Both the regression tests and the example PDF generation require the Python package `graphviz` and the Graphviz `dot` command.


Example
==

<!--- body --->

# 2023/8/18
## *pre1* Preprocess of X

Process X with Y for later procedure.

## *pre2* Preprocess of Z _[pre1]~_

Process Z with Y for later procedure.

## *mix* Mix X and Y@clean bench _15:00~_ <!-- pre2, pre1 -->

Mix X and Z and put it in the incubator for 30 min.

## *recordXZ* Record data of the mixture@microscope _mix+0:30~_ <!-- mix -->

Record data of the mixture using the microscope.

# 2023/8/22
## *sample* Make A from a sample

Make A from the today's sample.

## *record1* Record data of A@microscope <!-- sample -->

Record data of the today's sample.

## *mix2* Add A to XZ@clean bench <!-- record1,  recordXZ -->

Mix A to the mixture of XZ and put it in the incubator for 1 hour.

## *record2* Record data of AXZ@microscope _mix2+1:00~_ <!-- mix2 -->

Record data of the final composite.

## *clean*  Clean up@clean bench  <!--  record2  -->

Clean up the used tubes and dishes.


