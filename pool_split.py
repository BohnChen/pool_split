"""
pool_split.py —— 每日瓜分奖池的分账逻辑

优化后生产级实现：
采用最大余额法（Largest Remainder Method / Hamilton-Hare Method），全程基于纯整数运算，
消除浮点精度损失与 round() 引起的累积误差，严格保证总额守恒，兼顾数学公平性与确定性。
"""


def split_pool(pool_cents: int, weights: list[int]) -> list[int]:
    """把 pool_cents 按 weights 的比例分给每个人，返回每人拿到多少分。

    算法原理：最大余额法（纯整数计算）
    1. 计算每个人应得金额的整数基数 floor(pool_cents * w / total) 以及零头余数 (pool_cents * w % total)。
    2. 计算未分配差额 remainder = pool_cents - sum(base_amounts)。
    3. 按零头余数从大到小排序，余数相同的按原始输入索引从小到大稳定排序，前 remainder 个人各补 1 分。

    参数规约与容错（方案 B）：
    - 若 pool_cents < 0 或任意权重 < 0：抛出 ValueError。
    - 若 weights 为空：若 pool_cents == 0 返回 []，否则抛出 ValueError。
    - 若 pool_cents == 0：所有人分配 0 分。
    - 若权重总和为 0：若 pool_cents == 0 返回全 0，否则抛出 ValueError。

    :param pool_cents: 奖池总金额（单位：分，非负整数）
    :param weights: 每人贡献权重列表（非负整数）
    :return: 分配金额列表，与 weights 一一对应，和严格等于 pool_cents
    """
    if pool_cents < 0:
        raise ValueError(f"奖池总额不能为负数: pool_cents={pool_cents}")

    n = len(weights)
    if n == 0:
        if pool_cents == 0:
            return []
        raise ValueError("参与者列表为空，无法分配非零奖池")

    for i, w in enumerate(weights):
        if w < 0:
            raise ValueError(f"用户权重不能为负数: weights[{i}]={w}")

    # 奖池为 0，无论权重如何，所有人均分 0 分
    if pool_cents == 0:
        return [0] * n

    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("总权重为 0，无法按比例瓜分非零奖池")

    # 纯整数运算：避免浮点数精度截断
    # base_allocations: 下取整基数分配
    # remainders: 零头余数分子 (pool_cents * w % total_weight)
    base_allocations = [0] * n
    remainders = [0] * n

    for i, w in enumerate(weights):
        prod = pool_cents * w
        base_allocations[i] = prod // total_weight
        remainders[i] = prod % total_weight

    # 待分配的零头总分额
    allocated_sum = sum(base_allocations)
    remainder_cents = pool_cents - allocated_sum

    if remainder_cents > 0:
        # 稳定排序仲裁：按 (-余数, 原始索引) 排序
        # 优先补偿零头余数最大者；余数相同按原数组顺序（索引小优先）确定性补偿
        # 排序键：-remainder 正序等价于 remainder 降序；原始索引 index 自然升序
        sorted_indices = sorted(range(n), key=lambda idx: (-remainders[idx], idx))
        for k in range(remainder_cents):
            target_idx = sorted_indices[k]
            base_allocations[target_idx] += 1

    return base_allocations


def legacy_split_pool(pool_cents: int, weights: list[int]) -> list[int]:
    """未修改的原始分账实现（供测试对比及回归复现使用）"""
    total = sum(weights)
    return [round(pool_cents * w / total) for w in weights]


if __name__ == "__main__":
    print("示例 1 (10000 分平分给 3 人):", split_pool(10000, [1, 1, 1]))
    print("示例 2 (100 分平分给 3 人):", split_pool(100, [1, 1, 1]))
    print("示例 3 (5 分平分给 3 人):", split_pool(5, [1, 1, 1]))
