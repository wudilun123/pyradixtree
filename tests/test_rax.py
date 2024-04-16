import pytest
import math
import os
import sys
import time
from random import randint, random
from strgen import StringGenerator
from typing import Any, List, Iterator, Optional

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from src.pyradixtree.rax import RadixTree, RadixTreeNode

patterns = {
    'RANDOM_NUMBER': '[0-9]',
    'RANDOM_ALPHA': '[a-zA-Z]',
    'RANDOM_SMALL_CSET': '[ABCD]',
    'CHAIN': '[A]',
}


def random_strs(mod: str, str_len: int, count: int) -> List[str]:
    pattern = patterns[mod] + f'{{{str_len}}}'
    return StringGenerator(pattern).render_list(count)


def del_key_succeed(h: Any, key: str) -> bool:
    try:
        del h[key]
    except KeyError:
        return False
    else:
        return True


def iter_nodes(rax: RadixTree, root: Optional[RadixTreeNode] = None) -> Iterator[RadixTreeNode]:
    if root is None:
        root = rax.head
    yield root
    for key in root.sorted_edges():
        yield from iter_nodes(rax, root.children[key])


def rax_fuzz(mod: str, count: int, ins_prob: float, del_prob: float):
    rax = RadixTree()
    d = {}

    batch_size, inc = 1000, 0
    batch_num = math.ceil(count / batch_size)
    for i in range(batch_num):
        for key in random_strs(mod, randint(1, 16), min(batch_size, count)):
            if random() < ins_prob:
                rax[key] = inc
                d[key] = inc
                inc += 1
        for key in random_strs(mod, randint(1, 16), min(batch_size, count)):
            if random() < del_prob:
                assert del_key_succeed(rax, key) == del_key_succeed(d, key)
        count -= batch_size
        assert len(d) == len(rax)

    elem_cnt = 0
    for key in rax:
        assert rax[key] == d[key]
        elem_cnt += 1
    assert len(d) == elem_cnt

    for k1, k2 in zip(rax, sorted(d)):
        assert k1 == k2
        assert rax[k1] == d[k2]
    for k1, k2 in zip(reversed(rax), sorted(d, reverse=True)):
        assert k1 == k2
        assert rax[k1] == d[k2]

    for node in iter_nodes(rax):
        if node is rax.head:
            continue
        p = node.parent.not_key_with_single_child()
        n = node.not_key_with_single_child()
        assert not (p and n)  # There is no consecutive non-key node with single child.

    rax.clear()


@pytest.mark.fuzz
@pytest.mark.parametrize('mod', list(patterns.keys()))
def test_rax_fuzz(mod: str):
    if mod == 'CHAIN':
        rax_fuzz(mod, 1000, .7, .3)
        return

    count = 10000
    for i in range(10):
        ins_prob = random()
        rax_fuzz(mod, randint(count // 2, count), ins_prob, 1 - ins_prob)
    for i in range(3):
        rax_fuzz(mod, count, .7, .3)
        count *= 10


@pytest.mark.unit
def test_rax_ins_and_del():
    rax = RadixTree()
    count = 2000
    keys = random_strs('RANDOM_SMALL_CSET', 8, count)
    for key in keys:
        rax[key] = 0
    key_set = set(keys)
    assert len(rax) == len(key_set)
    for key in key_set:
        del rax[key]
    assert len(rax) == 0


@pytest.mark.unit
def test_rax_iter():
    rax = RadixTree()
    d = {}
    for key in random_strs('RANDOM_SMALL_CSET', 8, 2000):
        rax[key] = 0
        d[key] = 0
    assert len(rax) == len(d)
    for k1, k2 in zip(rax, sorted(d)):
        assert k1 == k2
    for k1, k2 in zip(reversed(rax), sorted(d, reverse=True)):
        assert k1 == k2
    rax.clear()


@pytest.mark.unit
def test_rax_methods():
    rax = RadixTree()
    d = {}
    key_list = ['PY', 'PYTHON', 'PYTEST', 'PTLIST', 'GO', 'GOLANG', 'GTEST']

    for i, key in enumerate(key_list):
        rax[key] = i
        d[key] = i
    assert len(rax) == len(d)
    assert list(rax) == list(sorted(d))
    assert list(rax.keys()) == sorted(d.keys())
    assert sorted(rax.values()) == sorted(d.values())
    assert list(rax.items()) == sorted(d.items())

    copied_rax = rax.copy()
    new_rax = RadixTree.fromkeys(d.keys(), -1)
    for key in d:
        assert rax[key] == d[key]
        assert copied_rax[key] == d[key]
        assert new_rax[key] == -1

    rem_key = key_list.pop()
    assert len(rax) - 1 == rax.pop(rem_key)
    assert rem_key not in rax
    for key in key_list:
        assert key in rax
    assert not rax.get('JAVA', False)
    assert rax.get('PYTHON') is not None

    key, val = rax.popitem()
    assert val == key_list.index(key)
    key_list.pop(key_list.index(key))
    rax.setdefault('JAVA', len(key_list))
    key_list.append('JAVA')
    assert rax['JAVA'] == key_list.index('JAVA')
    assert rax.setdefault('PYTHON') == key_list.index('PYTHON')
    rax.update({'PYTHON': -1})
    assert rax['PYTHON'] == -1

    rax.clear()


@pytest.mark.benchmark
@pytest.mark.parametrize('mod', list(patterns.keys())[:-1])
def test_rax_bench(mod: str):
    rax = RadixTree()
    d = {}
    batch, count = 100, 10000
    keys = random_strs(mod, randint(1, 16), count)
    key_set = set(keys)

    ins_t1, ins_t2 = 0, 0
    iter_t1, iter_t2 = 0, 0
    del_t1, del_t2 = 0, 0
    for i in range(batch):
        now_ns = time.perf_counter_ns()
        for key in keys:
            rax[key] = i
        ins_t1 += time.perf_counter_ns() - now_ns
        now_ns = time.perf_counter_ns()
        for key in keys:
            d[key] = i
        ins_t2 += time.perf_counter_ns() - now_ns
        assert rax == d

        now_ns = time.perf_counter_ns()
        for _ in rax:
            pass
        iter_t1 += time.perf_counter_ns() - now_ns
        now_ns = time.perf_counter_ns()
        for _ in d:
            pass
        iter_t2 += time.perf_counter_ns() - now_ns

        now_ns = time.perf_counter_ns()
        for key in key_set:
            del rax[key]
        del_t1 += time.perf_counter_ns() - now_ns
        now_ns = time.perf_counter_ns()
        for key in key_set:
            del d[key]
        del_t2 += time.perf_counter_ns() - now_ns
        assert len(rax) == 0
    print(f'\nAverage ms after {count} insert: rax {ins_t1 // 1e6} & dict {ins_t2 // 1e6}.')
    print(f'Average ms after iterate {count} keys: rax {iter_t1 // 1e6} & dict {iter_t2 // 1e6}.')
    print(f'Average ms after {count} delete: rax {del_t1 // 1e6} & dict {del_t2 // 1e6}.')
