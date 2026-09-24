"""
test_pool_split.py —— 奖池分账逻辑测试套件
"""

import unittest
from pool_split import split_pool


class TestPoolSplit(unittest.TestCase):
    def test_total_conservation_basic(self):
        """测试基础守恒性：所有人拿到的金额之和必须等于池子总额。"""
        # 反例 1：100 分分给 3 个权重相同的人
        # 100 * 1/3 = 33.333... -> round 后为 33
        # 实际和: 33 + 33 + 33 = 99 != 100
        pool_cents = 100
        weights = [1, 1, 1]
        result = split_pool(pool_cents, weights)
        self.assertEqual(
            sum(result),
            pool_cents,
            f"分账结果之和不等于奖池总额！输入: pool_cents={pool_cents}, weights={weights}, "
            f"分配结果: {result}, 实际和: {sum(result)}, 应有和: {pool_cents}",
        )

    def test_total_conservation_excess(self):
        """测试多发钱反例：round 向上取整导致总和超标。"""
        # 反例 2：5 分分给 3 个权重相同的人
        # 5 * 1/3 = 1.666... -> round 后为 2
        # 实际和: 2 + 2 + 2 = 6 != 5
        pool_cents = 5
        weights = [1, 1, 1]
        result = split_pool(pool_cents, weights)
        self.assertEqual(
            sum(result),
            pool_cents,
            f"分账结果之和不等于奖池总额！输入: pool_cents={pool_cents}, weights={weights}, "
            f"分配结果: {result}, 实际和: {sum(result)}, 应有和: {pool_cents}",
        )


if __name__ == "__main__":
    unittest.main()
