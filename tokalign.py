# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import heapq
import logging
import sys

from functools import total_ordering


class LinkSame:
    def __init__(self, cost):
        self.cost = cost

    def apply(self, hypo, txt1, txt2):
        if hypo.pos1 >= 0 or hypo.pos2 >= 0:
            return None

        if txt1[hypo.pos1] == txt2[hypo.pos2]:
            ext = (hypo.pos1 + len(txt1), hypo.pos2 + len(txt2))
            return Hypothesis(hypo.cost + self.cost, hypo.pos1 + 1, hypo.pos2 + 1, ext, hypo)
        else:
            return None


class LinkDifferent:
    def __init__(self, cost):
        self.cost = cost

    def apply(self, hypo, txt1, txt2):
        if hypo.pos1 >= 0 or hypo.pos2 >= 0:
            return None

        if txt1[hypo.pos1] != txt2[hypo.pos2]:
            ext = (hypo.pos1 + len(txt1), hypo.pos2 + len(txt2))
            return Hypothesis(hypo.cost + self.cost, hypo.pos1 + 1, hypo.pos2 + 1, ext, hypo)
        else:
            return None
        

class Skip1:
    def __init__(self, cost):
        self.cost = cost

    def apply(self, hypo, txt1, txt2):
        if hypo.pos1 >= 0:
            return None

        ext = (hypo.pos1 + len(txt1), None)
        return Hypothesis(hypo.cost + self.cost, hypo.pos1 + 1, hypo.pos2, ext, hypo)


class Skip2:
    def __init__(self, cost):
        self.cost = cost

    def apply(self, hypo, txt1, txt2):
        if hypo.pos2 >= 0:
            return None

        ext = (None, hypo.pos2 + len(txt2))
        return Hypothesis(hypo.cost + self.cost, hypo.pos1, hypo.pos2 + 1, ext, hypo)


@total_ordering
class Hypothesis:
    def __init__(self, cost, pos1, pos2, alignment, prev):
        self.cost = cost
        self.pos1 = pos1
        self.pos2 = pos2
        self.alignment = alignment
        self.prev = prev
        self.total_cost = self.cost + self._future_cost(pos1, pos2)
        self.discarded = False

    def recombination_key(self):
        return (self.pos1, self.pos2, self.alignment)

    def _future_cost(self, pos1, pos2):
        return abs(pos1 - pos2)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "Hypothesis(%.2f, %.2f, %d, %d, %s)" % (self.total_cost, self.cost, self.pos1, self.pos2, self.alignment)

    def __eq__(self, other):
        return self.total_cost == other.total_cost

    def __lt__(self, other):
        return self.total_cost < other.total_cost
    

def align(txt1, txt2):
    ops = [LinkSame(0.0), LinkDifferent(1.0), Skip1(2.0), Skip2(2.0)]

    queue = [Hypothesis(0.0, -len(txt1), -len(txt2), None, None)]
    recomb = {}

    while True:
        hypo = heapq.heappop(queue)
        if hypo.discarded:
            continue

        logging.debug("Expanding:" + str(hypo))

        if hypo.pos1 == 0 and hypo.pos2 == 0:
            break

        for op in ops:
            updated = op.apply(hypo, txt1, txt2)
            if updated is not None:
                existing = recomb.get(updated.recombination_key())
                if existing is None:
                    logging.debug("Adding: " + str(updated))
                    heapq.heappush(queue, updated)
                    recomb[updated.recombination_key()] = updated
                elif existing.total_cost > updated.total_cost:
                    logging.debug("Recombining: " + str(updated))
                    existing.discarded = True
                    heapq.heappush(queue, updated)
                    recomb[updated.recombination_key()] = updated
                else:
                    logging.debug("Discarding: " + str(updated))

    alignments = []
    while hypo is not None:
        if hypo.alignment is not None:
            alignments.append(hypo.alignment)
        hypo = hypo.prev

    alignments.reverse()
    return alignments


def main():
    logging.basicConfig(format='%(asctime)s %(message)s')

    if len(sys.argv) != 3:
        print("Usage: tokalign.py file1 file2", file=sys.stderr)
        sys.exit(1)

    filename1 = sys.argv[1]
    filename2 = sys.argv[2]

    with open(filename1, 'r') as f:
        txt1 = f.read().split()

    with open(filename2, 'r') as f:
        txt2 = f.read().split()

    print(align(txt1, txt2))


if __name__ == "__main__":
    main()
