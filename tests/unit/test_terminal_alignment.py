from collections import Counter
from itertools import permutations
import random
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'web/backend'))
from app.alignment import maximum_overlap


class AlignmentTests(unittest.TestCase):
    def test_rectangular_sparse_ids_unmatched_and_noise(self):
        counts=Counter({(2,5):5,(8,11):8,(2,20):1,(-1,30):50})
        mapping,left,right=maximum_overlap(counts,[-1,2,8],[5,11,20,30])
        self.assertEqual(mapping,{5:2,11:8})
        self.assertEqual(left,[]);self.assertEqual(right,[20,30])
        self.assertEqual(maximum_overlap({},[0,3],[4]),({},[0,3],[4]))

    def test_matches_exhaustive_optimum_on_small_rectangles(self):
        rng=random.Random(42)
        for rows,cols in ((2,4),(4,2),(3,3),(1,4)):
            weights=Counter({(i,j):rng.randrange(10) for i in range(rows) for j in range(cols)})
            mapping,_,_=maximum_overlap(weights,range(rows),range(cols))
            actual=sum(weights[source,target] for target,source in mapping.items())
            size=max(rows,cols)
            expected=max(sum(weights.get((i,perm[i]),0) for i in range(rows)) for perm in permutations(range(size)))
            self.assertEqual(actual,expected)

    def test_large_k_does_not_enumerate_permutations(self):
        mapping,_,_=maximum_overlap(Counter({(i,100+i):i+1 for i in range(50)}),range(50),range(100,150))
        self.assertEqual(mapping,{100+i:i for i in range(50)})

if __name__=='__main__':unittest.main()
