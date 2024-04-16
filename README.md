# 简介
`pyradixtree`库是完全使用`Python`编写的一种基数树实现，其参考了`Redis`中的基数树实现[RAX, an ANSI C radix tree implementation](https://github.com/redis/redis/blob/unstable/src/rax.c)并扩展了部分内容。
由于纯`Python`实现与`C`实现性能存在数量级差距，且为了实现方便，节点所占内存保有优化空间，**此库仅可用于练习使用**。

# 环境要求
```
库运行：
Python解释器版本 >= 3.8

测试代码运行：
需安装库 Pytest,StringGenerator
```

# 基本用法
模块仅提供类`RadixTree`，它继承自`MutableMapping`并实现了全部接口，是自定义的映射类型，使用类似于只支持`str`类型键的`Dict`。
安装：
```shell
pip install pyradixtree
```
使用：
```python
from pyradixtree import RadixTree

rax = RadixTree()
keys = ['a', 'b', 'c']
for i, key in enumerate(keys):
    rax[key] = i

# a 0
# b 1
# c 2
for key in rax:
    print(key, rax[key])

del rax['a']
print('a' not in rax)  # True
```

# 功能
`RadixTree`支持了`Dict`支持的所有操作，详情可参考[内置类型: Dict](https://docs.python.org/zh-cn/3.8/library/stdtypes.html#mapping-types-dict)。

下面列举了`RadixTree`支持的全部操作：
- **`rax[key]`** 返回基数树中`key`对应节点存放的值，若`key`不存在则引发`KeyError`。

- **`rax[key] = value`** 将`key`对应节点的值设为`value`。

- **`del rax[key]`** 将`key`对应节点从基数树中删除，若`key`不存则引发`KeyError`。

- **`key in rax | key not in rax`** 判断`key`是否存在于基数树中。

- **`list(rax)`** 返回基数树中全部键组成的列表(有序)。

- **`len(rax)`** 返回基数树的元素数量(键个数)。

- **`iter(rax)`** 返回以基数树的键为元素的迭代器(保证字典升序)，效果同`iter(rax.keys())`。

- **`reversed(rax)`** 返回一个以基数树的键为元素的逆序迭代器(字典序倒序)。

- **`rax.clear()`** 删除基数树中全部元素。

- **`rax.copy()`** 返回基数树的浅拷贝。

- **`classmethod fromkeys(iterable[,value])`** 使用可迭代的`iterable`作为键创建一个新基数树，并将键值都设为`value`(默认为`None`)。

- **`get(key[,default])`** 如果`key`存在则返回对应节点存放的值，否则返回`default`(默认为`None`)。

- **`rax.keys()`** 返回由基数树全部的键组成的视图对象。

- **`rax.values()`** 返回由基数树全部的元素值组成的视图对象。

- **`rax.items()`** 返回由基数树全部的键值对组成的视图对象。

- **`rax.pop()`** 如果`key`存在则删除对应节点并返回值，否则返回`default`。若`default`未给出且`key`不存在则引发`KeyError`。

- **`rax.popitem()`** 从基数树中删除一个键节点并返回键值对，返回顺序由键字典序决定。

- **`rax.setdefault(key[,default])`** 如果`key`存在则返回对应节点的值，否则插入值为`default`的键`key`并返回`default`(默认为`None`)。

- **`rax.update([other])`** 使用来自`other`的键值对更新基数树，若键原本存在则更新值。它接收一个字典对象或包含键值对的可迭代对象，如果给出关键字参数则会以此更新字典：`rax.update(a=1, b=2)`。

另外，两个`RadixTree`之间支持`==`比较，当二者键值对完全相同时等式成立。

# 测试运行
测试使用`pytest`框架运行，使用`StringGenrator`库来随机生成字符串
```shell
运行全部测试：
pip install pytest, StringGenrator
pytest -vs

根据测试标记过滤用例：fuzz/unit/benchmark
pytest -vs -m fuzz
pytest -vs -m unit
pytest -vs -m benchmark
其中benchmark测试未使用pytest-benchmark插件

生成覆盖率报告
pip install pytest-cov
pytest -vs --cov --cov-report=html
```

# 存在的问题
1. 使用纯`Python`实现，性能较C库相差数量级的差距，仅可作为“玩具”使用。
2. 仅就`Python`来说，对于节点中出边、入边和父节点的存储存在较大优化空间，目前是为了方便实现，实际内存开销可能还不如其它映射数据结构，也就失去了使用基数树的意义。
3. 节点间存在循环引用的问题，`GC`回收性能可能受影响。