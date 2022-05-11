panda3d-trees
-------------

A module for creating geometry and materials of botanical trees. This is
a (currently very partial and apparently somewhat incorrect)
implementation of "Creation and Rendering of Realistic Trees"
(Weber, Penn, 1995).

I intend to refactor the code and generalize its approach, so that the
implementation is not a mess of special case formulas.


Theory
------

A tree consists of stems which in turn consists of segments. The tree is
defined as several layers of stems (e.g. trunk, branches, twigs), each
being created using a different set of parameters.

A stem is more or less S-shaped in Weber/Penn, either bending one way,
or one way, then the other. 