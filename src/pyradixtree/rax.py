from collections.abc import MutableMapping
from typing import Any, Callable, Dict, Iterator, List, Tuple, Type, Optional


def check_key_type(t: Type) -> Callable:
    # 用于检查radix tree的键的类型
    def decorator(func: Callable) -> Callable:
        def wrapper(rax: 'RadixTree', key: str, *args, **kwargs) -> Any:
            if not isinstance(key, t):
                raise TypeError(f'Key must be {t.__name__}, not {type(key).__name__}.')
            return func(rax, key, *args, **kwargs)

        return wrapper

    return decorator


class RadixTreeNode:
    def __init__(self, is_key: bool = False):
        self.is_key = is_key
        self.children: Dict[str, Any] = {}
        self.parent: Optional[RadixTreeNode] = None
        self.edge: Optional[str] = None  # 存储节点入边
        self.data: Any = None

    def add_child(self, edge: str, node: 'RadixTreeNode'):
        edge_len = len(edge)
        if self.is_compressed() or edge_len == 0:
            return
        if edge_len > 1 and not self.has_no_child():
            return
        self.children[edge] = node
        node.parent = self
        node.edge = edge

    def remove_child(self, child: 'RadixTreeNode'):
        if (edge := child.edge) is None:
            return
        del self.children[edge]
        child.parent = None
        child.edge = None

    def remove_all_children(self):
        self.children.clear()

    def children_num(self) -> int:
        return len(self.children)

    def has_no_child(self) -> bool:
        return self.children_num() == 0

    def not_key_with_single_child(self) -> bool:
        return not self.is_key and self.children_num() == 1

    def sorted_edges(self, reverse: bool = False) -> Iterator[str]:
        return iter(sorted(self.children, reverse=reverse))

    def set_data(self, data: Any):
        self.data = data

    def get_data(self) -> Any:
        return self.data

    def is_compressed(self) -> bool:
        return self.children_num() == 1 and len(self.single_edge()) > 1

    def single_edge(self) -> str:
        return next(iter(self.children.keys()))  # 使用时确保只有单个孩子


class RadixTree(MutableMapping):
    def __init__(self):
        self.head = RadixTreeNode()
        self.elem_cnt = 0
        self.node_cnt = 0

    @check_key_type(str)
    def __getitem__(self, key: str) -> Any:
        return self._find_key_node(key).get_data()

    @check_key_type(str)
    def __setitem__(self, key: str, value: Any):
        self._insert_key_node(key, value)

    @check_key_type(str)
    def __delitem__(self, key: str):
        self._delete_key_node(key)

    @check_key_type(str)
    def __contains__(self, key: str) -> bool:
        try:
            self.__getitem__(key)
        except KeyError:
            return False
        else:
            return True

    def __iter__(self) -> Iterator[str]:
        return self._iter_key_nodes()

    def __reversed__(self) -> Iterator[str]:
        return self._reversed_key_nodes()

    def __len__(self) -> int:
        return self.elem_cnt

    def clear(self):
        """
        删除radix tree中所有节点(包含所有键值)
        """
        self.head.remove_all_children()
        self.elem_cnt = 0
        self.node_cnt = 0

    def copy(self) -> 'RadixTree':
        """
        得到radix tree的浅拷贝
        :return: 本radix tree的浅拷贝
        """
        copied = RadixTree()
        for key in self:
            copied[key] = self[key]
        return copied

    @classmethod
    def fromkeys(cls, iterable: Iterator[str], value: Optional[any] = None) -> 'RadixTree':
        """
        根据可迭代的键和可选的值来构造新的radix tree
        :param iterable: 可迭代的键，类型必须是字符串
        :param value: 可选的值，为所有键节点赋予相同的值，默认为None
        :return: 构造好的radix tree
        """
        rax = RadixTree()
        for key in iterable:
            rax[key] = value
        return rax

    def _low_walk(self, key: str) -> Tuple[RadixTreeNode, int, int]:
        """
        这是一个低级别函数，用于在radix tree中匹配指定的键
        :param key: 待匹配的键
        :return: 共有三个返回值，首个为匹配结束时所在的节点，其次是成功匹配的长度，最后是在压缩节点中间停止匹配的位置
        """
        i, j = 0, 0
        cur, key_len = self.head, len(key)
        while not cur.has_no_child() and i < key_len:
            edge, i, j = self._match_edge(key, i, cur)
            if not edge:
                break
            cur = cur.children[edge]
        return cur, i, j

    @staticmethod
    def _match_edge(key: str, pos: int, cur: RadixTreeNode) -> Tuple[Optional[str], int, int]:
        """py
        匹配当前节点的出边
        :param key: 待匹配的键
        :param pos: 匹配起始位置
        :param cur: 当前节点
        :return: 共有三个返回值，首个为匹配成功的边，失败则为None，其次是匹配结束位置，最后是在压缩节点中间停止匹配的位置
        """
        key_len = len(key)
        if cur.is_compressed():
            edge = cur.single_edge()
            for i in range(len(edge)):
                if pos >= key_len or edge[i] != key[pos]:
                    return None, pos, i
                pos += 1
            return edge, pos, 0
        else:
            edges = list(cur.children.keys())
            for i in range(len(edges)):
                if edges[i] == key[pos]:
                    pos += 1
                    return edges[i], pos, 0
            return None, pos, 0

    def _insert_key_node(self, key: str, value: Any):
        """
        向radix tree插入键节点
        :param key: 待插入的键
        :param value: 待插入的值
        """
        cur, i, j = self._low_walk(key)
        is_compr, key_len = cur.is_compressed(), len(key)
        if i == key_len and (not is_compr or j == 0):
            # 匹配成功且当前节点无需切割
            cur.set_data(value)
            if not cur.is_key:
                cur.is_key = True
                self.elem_cnt += 1
            return

        if is_compr:
            if (split_node := self._split_compressed_node(i == key_len, j, cur, value)) is None:
                return
            cur = split_node

        while i < key_len:
            child = RadixTreeNode()
            if cur.has_no_child() and (compr_len := key_len - i) > 1:
                # 当前节点无孩子且待处理的键长超过1，转换为压缩节点
                cur.add_child(key[i:], child)
                i += compr_len
            else:
                cur.add_child(key[i], child)
                i += 1
            self.node_cnt += 1
            cur = child

        cur.set_data(value)
        cur.is_key = True
        self.elem_cnt += 1

    def _split_compressed_node(self, key_match_end: bool, trimmed_len: int, cur: RadixTreeNode,
                               data: Any) -> Optional[RadixTreeNode]:
        """
        根据键是否匹配完成来区分处理
        :param key_match_end: 区分键是否匹配完成的情况
        :param trimmed_len: 当前节点拆分完后的剩余长度，等于压缩节点中间停止匹配的位置
        :param cur: 当前节点
        :param data: 待存储数据
        :return: 当键未匹配完成时，返回的是拆分节点，流程继续处理，反之返回None
        """
        edge = cur.single_edge()
        child = cur.children[edge]
        cur.remove_child(child)
        if not key_match_end:
            postfix_len = len(edge) - trimmed_len - 1
            split_node = cur if trimmed_len == 0 else RadixTreeNode()
            postfix_node = child if postfix_len == 0 else RadixTreeNode()

            if trimmed_len != 0:
                # 切割压缩节点
                cur.add_child(edge[:trimmed_len], split_node)
                self.node_cnt += 1  # split_node

            split_node.add_child(edge[trimmed_len], postfix_node)

            if postfix_len != 0:
                postfix_node.add_child(edge[trimmed_len + 1:], child)
                self.node_cnt += 1

            return split_node
        else:
            postfix_node = RadixTreeNode(True)
            cur.add_child(edge[:trimmed_len], postfix_node)
            postfix_node.add_child(edge[trimmed_len:], child)
            postfix_node.set_data(data)
            self.elem_cnt += 1
            self.node_cnt += 1

            return None

    def _find_key_node(self, key: str) -> RadixTreeNode:
        """
        从radix tree中查找键节点，若节点不存在则抛出KeyError异常
        :param key: 待查找的键
        :return: 查找到的节点
        """
        cur, i, j = self._low_walk(key)
        if i != len(key) or (cur.is_compressed() and j != 0) or not cur.is_key:
            # 代表三种匹配失败情况：提前中止/停在压缩节点中间/非键节点
            raise KeyError(f"Key '{key}' was not found in the radix tree.")
        return cur

    def _delete_key_node(self, key: str):
        """
        从radix tree删除键节点，若节点不存在则抛出KeyError异常
        :param key: 待删除的键
        """
        cur, i, j = self._low_walk(key)
        if i != len(key) or (cur.is_compressed() and j != 0) or not cur.is_key:
            # 代表三种匹配失败情况：提前中止/停在压缩节点中间/非键节点
            raise KeyError(f"Key '{key}' was not found in the radix tree.")

        cur.set_data(None)
        cur.is_key = False
        self.elem_cnt -= 1

        if cur.has_no_child():
            # 当前节点无孩子，向上遍历删除所有只有一个孩子且非键的节点
            while parent := cur.parent:
                parent.remove_child(cur)
                self.node_cnt -= 1
                cur = parent
                if cur.is_key or not cur.has_no_child():
                    break

        if cur.not_key_with_single_child():
            # 当前节点非键且只有一个孩子，尝试与相邻节点合并
            self._try_compress(cur)

    def _try_compress(self, cur: RadixTreeNode):
        """
        尝试合并节点，保证radix tree中不存在连续的非键单孩子节点
        :param cur: 当前节点
        """
        while (parent := cur.parent) and parent.not_key_with_single_child():
            # 向上找到可以合并的首个节点
            cur = parent

        start, path, count = cur, [], 0
        if parent and parent.children_num() == 1:  # 对于仅有单孩子的键节点，也进行合并
            start = parent
            path.append(cur.edge)
            count += 1
        while cur.not_key_with_single_child():
            edge = cur.single_edge()
            path.append(edge)
            count += 1
            cur = cur.children[edge]

        if count <= 1:
            return
        start.remove_all_children()
        start.add_child(''.join(path), cur)
        self.node_cnt -= count - 1

    def _relink_parent2child(self, cur: RadixTreeNode, new: RadixTreeNode):
        """
        修改当前节点的父节点对子节点的引用，若当前节点为根节点则修改根节点的引用
        :param cur: 当前节点
        :param new: 修改后的子节点
        """
        if (parent := cur.parent) is None:
            self.head = new
        elif edge := cur.edge:
            parent.children[edge] = new
            new.parent = parent
            new.edge = edge
        else:
            return
        cur.parent = None
        cur.edge = None

    def _iter_key_nodes(self) -> Iterator[str]:
        """
        正向迭代radix tree
        :return: radix tree键的正序迭代器
        """
        cur = self.head
        on_search = False  # 表明是否在向上寻找可用节点的过程中
        path: List[str] = []  # 当前节点对应的路径
        edges_stack = [list(cur.sorted_edges())]  # 栈中存储了排序过的节点出边
        idx_stack = [-1]  # 栈中存储了上次访问出边的索引，和edges_stack配合使用来获取下次访问的节点出边

        while True:
            if on_search or cur.has_no_child():
                if cur is self.head:  # 迭代结束
                    return
                cur = cur.parent  # 转移至父节点尝试寻找
                path.pop()
                edges_stack.pop()
                idx_stack.pop()

            idx_stack[-1] += 1  # 访问下一个子节点
            edges, idx = edges_stack[-1], idx_stack[-1]
            if idx >= len(edges):  # 子节点均被访问过，继续向上寻找
                on_search = True
                continue
            on_search = False

            path.append(edges[idx])
            cur = cur.children[edges[idx]]
            edges_stack.append(list(cur.sorted_edges()))
            idx_stack.append(-1)
            if cur.is_key:
                yield ''.join(path)

    def _reversed_key_nodes(self) -> Iterator[str]:
        """
        反向迭代radix tree
        :return: radix tree键的逆序迭代器
        """

        def _seek_greatest():
            # 尝试转移到当前节点的最右子节点(对应的键在以当前节点为根节点的子树中最大)
            nonlocal cur
            while True:
                edges_stack.append(list(cur.sorted_edges(reverse=True)))
                idx_stack.append(0)
                if cur.has_no_child():
                    break
                last_edge = max(cur.children)
                path.append(last_edge)
                cur = cur.children[last_edge]

        cur = self.head
        path: List[str] = []
        edges_stack: List[List[str]] = []  # 栈中存储了排序过的节点出边
        idx_stack: List[int] = []  # 栈中存储了上次访问出边的索引，和edges_stack配合使用来获取下次访问的节点出边
        _seek_greatest()  # 迭代由radix tree的最右子节点开始

        while True:
            if cur.is_key:
                yield ''.join(path)
            if cur is self.head:  # 迭代结束
                return
            cur = cur.parent  # 转移至父节点尝试寻找
            path.pop()
            edges_stack.pop()
            idx_stack.pop()

            idx_stack[-1] += 1  # 访问下一个子节点
            edges, idx = edges_stack[-1], idx_stack[-1]
            if idx < len(edges):
                path.append(edges[idx])
                cur = cur.children[edges[idx]]
                _seek_greatest()  # 先从子节点的最右子节点开始寻找
