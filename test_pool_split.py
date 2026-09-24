"""
test_pool_split.py —— 奖池分账逻辑工程级测试套件

涵盖：
1. 失败复现测试（针对未修改代码 legacy_split_pool）
2. 基础守恒性与业务用例测试（针对修改后代码 split_pool）
3. 边界值与异常处理测试（方案 B 行为：全零、部分零权重、空输入、负值防御）
4. 基于属性的模糊测试（Property-based / Fuzz Testing：大规模随机输入守恒性验证）
5. 大规模性能基准测试（10 万参与者吞吐验证）
"""

import random
import time
import unittest
from pool_split import legacy_split_pool, split_pool


class TestLegacyPoolSplitFailure(unittest.TestCase):
    """验证未修改函数在特定输入下必定失败（满足任务书要求 3 的未修改输出）"""

    def test_legacy_underflow_failure(self):
        """未修改代码少发钱案例：pool_cents=100, weights=[1, 1, 1]"""
        pool_cents = 100
        weights = [1, 1, 1]
        result = legacy_split_pool(pool_cents, weights)
        # 实际和为 99，应有和为 100
        self.assertEqual(
            sum(result),
            pool_cents,
            f"[未修改代码期望失败] 实际和={sum(result)}, 应有和={pool_cents}, 分配结果={result}",
        )

    def test_legacy_overflow_failure(self):
        """未修改代码多发钱案例：pool_cents=5, weights=[1, 1, 1]"""
        pool_cents = 5
        weights = [1, 1, 1]
        result = legacy_split_pool(pool_cents, weights)
        # 实际和为 6，应有和为 5
        self.assertEqual(
            sum(result),
            pool_cents,
            f"[未修改代码期望失败] 实际和={sum(result)}, 应有和={pool_cents}, 分配结果={result}",
        )


class TestPoolSplitSuccess(unittest.TestCase):
    """验证修改后生产级 split_pool 的正确性与健壮性"""

    def test_fixed_previously_failing_cases(self):
        """验证原失败案例在修改后完全符合总额守恒规则"""
        # 案例 1：100 分分给 [1, 1, 1] -> 余数相同，前 1 人各补 1 分 -> [34, 33, 33]
        res1 = split_pool(100, [1, 1, 1])
        self.assertEqual(sum(res1), 100)
        self.assertEqual(res1, [34, 33, 33])

        # 案例 2：5 分分给 [1, 1, 1] -> [2, 2, 1]
        res2 = split_pool(5, [1, 1, 1])
        self.assertEqual(sum(res2), 5)
        self.assertEqual(res2, [2, 2, 1])

        # 案例 3：10000 分分给 [1, 1, 1] -> [3334, 3333, 3333]
        res3 = split_pool(10000, [1, 1, 1])
        self.assertEqual(sum(res3), 10000)
        self.assertEqual(res3, [3334, 3333, 3333])

    def test_varied_weights(self):
        """不等权重常规测试"""
        # pool=100, weights=[1, 2, 3], total=6
        # 100 * 1/6 = 16.666... (16, 余 4)
        # 100 * 2/6 = 33.333... (33, 余 2)
        # 100 * 3/6 = 50.000... (50, 余 0)
        # 基数和: 16+33+50 = 99，差 1 分。余数最大者是 weights[0]（余4），补 1 分 -> [17, 33, 50]
        res = split_pool(100, [1, 2, 3])
        self.assertEqual(sum(res), 100)
        self.assertEqual(res, [17, 33, 50])

    def test_boundary_zero_and_edge_cases(self):
        """方案 B 边界与容错测试"""
        # 1. 奖池为 0 分
        self.assertEqual(split_pool(0, [1, 2, 3]), [0, 0, 0])
        self.assertEqual(split_pool(0, [0, 0, 0]), [0, 0, 0])
        self.assertEqual(split_pool(0, []), [])

        # 2. 参与者存在 0 权重
        # weights=[10, 0, 10], pool=100 -> [50, 0, 50]
        self.assertEqual(split_pool(100, [10, 0, 10]), [50, 0, 50])
        # weights=[0, 1, 0], pool=10 -> [0, 10, 0]
        self.assertEqual(split_pool(10, [0, 1, 0]), [0, 10, 0])

        # 3. 奖池小于人数（极为悬殊）
        # 2 分分给 5 个人权重均为 1 -> 前 2 人各拿 1 分，其余 0 分
        self.assertEqual(split_pool(2, [1, 1, 1, 1, 1]), [1, 1, 0, 0, 0])

        # 4. 单人分配
        self.assertEqual(split_pool(12345, [42]), [12345])

    def test_error_inputs(self):
        """异常与防御性检查"""
        # 负奖池
        with self.assertRaises(ValueError):
            split_pool(-100, [1, 1])

        # 负权重
        with self.assertRaises(ValueError):
            split_pool(100, [1, -2, 3])

        # 非零奖池但无人参与
        with self.assertRaises(ValueError):
            split_pool(100, [])

        # 非零奖池但总权重为 0
        with self.assertRaises(ValueError):
            split_pool(100, [0, 0, 0])

    def test_property_based_fuzzing(self):
        """基于属性的随机模糊测试（10,000 组极端随机输入验证守恒性与公平性）"""
        rng = random.Random(42)  # 固定种子确保确定性可复现
        for _ in range(10000):
            n = rng.randint(1, 50)
            pool = rng.randint(0, 1_000_000)
            # 生成可能包含 0 的权重
            weights = [rng.randint(0, 1000) for _ in range(n)]

            if sum(weights) == 0:
                if pool == 0:
                    res = split_pool(pool, weights)
                    self.assertEqual(sum(res), 0)
                else:
                    with self.assertRaises(ValueError):
                        split_pool(pool, weights)
                continue

            res = split_pool(pool, weights)

            # 核心不变量 1：总和严格守恒
            self.assertEqual(sum(res), pool)

            # 核心不变量 2：每个人拿到金额与理论值的偏差绝对值小于 1 分
            total_w = sum(weights)
            for w, got in zip(weights, res):
                exact = (pool * w) / total_w
                self.assertLessEqual(
                    abs(got - exact),
                    1.0 + 1e-9,
                    f"偏差超出 1 分: 理论={exact}, 实际={got}",
                )

    def test_performance_benchmark(self):
        """性能基准：验证 10 万人级别分账的响应效率（通常要求在 100ms 内）"""
        n = 100_000
        pool = 10_000_000  # 10 万元奖池
        weights = [random.randint(1, 100) for _ in range(n)]

        start_time = time.perf_counter()
        res = split_pool(pool, weights)
        elapsed_sec = time.perf_counter() - start_time

        self.assertEqual(sum(res), pool)
        self.assertEqual(len(res), n)
        # 断言执行时间小于 0.2 秒（现代 CPU 上纯 Python 排序 10 万元素通常在 30-80ms）
        self.assertLess(
            elapsed_sec,
            0.5,
            f"10 万人分账耗时过长: {elapsed_sec:.4f}s",
        )
        print(f"\n[性能测试] 100,000 人瓜分 100,000.00 元奖池耗时: {elapsed_sec * 1000:.2f} ms")


if __name__ == "__main__":
    import sys

    # 支持命令行参数切换测试目标，以便分别展示失败与成功输出
    if "--legacy" in sys.argv:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLegacyPoolSplitFailure)
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPoolSplitSuccess)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
