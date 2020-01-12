import unittest

from pyperaptor import Device, Node, Pipeline
from pyperaptor.pipeline import LockedPipelineError, UnlockedPipelineError

class TestDevice(unittest.TestCase):
    def test_device_creation(self):
        d = Device("a name")
        assert (d is not None) and (d.name == "a name")

        d = Device("a name", 3)
        assert (d is not None) and (d.name == "a name" and d.__sem__._value == 3)

    def test_device_lock(self):
        d = Device("another name", 2)
        d.get()
        assert (d.__sem__._value == 1)
        d.get()
        assert (d.__sem__._value == 0)
        d.release()
        assert (d.__sem__._value == 1)
        d.release()
        assert (d.__sem__._value == 2)

class TestNode(unittest.TestCase):
    def test_node_creation(self):
        def zfunc():
            return 0

        def yfunc():
            return 1

        n = Node(zfunc)
        assert isinstance(n, Node)
        assert n.get_fn() == zfunc

        m = Node(yfunc)
        z = n + n
        assert m.get_fn() == yfunc
        assert isinstance(z, Pipeline)

    def test_node_with_device(self):
        def zfunc():
            return 0

        def yfunc():
            return 1

        device_a = Device("A")
        n = Node(zfunc, dev=device_a)
        n.obtain_device()
        assert n._dev.__sem__._value == 0
        n.return_device()
        assert n._dev.__sem__._value == 1

class TestNode(unittest.TestCase):
    def test_pipeline_creation(self):
        p = Pipeline()
        assert isinstance(p, Pipeline) and (p.__max_workers__ == 1) and (p.process.__func__.__name__ == "__single_process")
        
        fs = [
            (lambda x: 0),
            (lambda x: 0)
        ]

        p = Pipeline(fs)
        assert len(p.__tasks__) == 2

        p = Pipeline(parallel = True, workers=3)
        assert isinstance(p, Pipeline) and (p.__max_workers__ == 3) and (p.process.__func__.__name__ == "__parallel_process")

    def test_pipeline_node_adding(self):
        def zfunc():
            return 0

        def yfunc():
            return 1

        p = Pipeline()
        assert len(p.__tasks__) == 0

        p.add(zfunc)
        assert len(p.__tasks__) == 1

        p.add(zfunc)
        assert len(p.__tasks__) == 2

        p = Pipeline()
        assert len(p.__tasks__) == 0

        p += Node(zfunc)
        assert len(p.__tasks__) == 1

        p += Node(yfunc)
        assert len(p.__tasks__) == 2

        p = Pipeline()
        assert len(p.__tasks__) == 0

        list(map(p.add, [zfunc, yfunc]))
        assert len(p.__tasks__) == 2

    def test_pipeline_adding_pipelines(self):
        def zfunc():
            return 0

        def yfunc():
            return 1

        p = Pipeline([zfunc])
        q = Pipeline([yfunc])

        p += q
        assert len(p.__tasks__) == 2

    def test_pipeline_is_locked_before_execution(self):
        def zfunc():
            return 0

        p = Pipeline([zfunc])
        with self.assertRaises(UnlockedPipelineError) as context:
            p.push()


    def test_pipeline_push_no_args(self):
        def zero():
            return 0

        def one():
            return 1

        p = Pipeline([zero])
        p.lock()
        result = p.push()
        assert result == 0

        p = Pipeline([zero, one])
        p.lock()
        result = p.push()
        assert result == 1

    def test_pipeline_push_with_args(self):
        def sum1(x):
            return x + 1

        p = Pipeline([sum1])
        p.lock()
        result = p.push(0)
        assert result == 1

        p = Pipeline([sum1, sum1, sum1])
        p.lock()
        result = p.push(0)
        assert result == 3

    def test_pipeline_push_no_args_no_return(self):
        def void():
            pass

        p = Pipeline([void])
        p.lock()
        result = p.push()
        assert result is None

    def test_pipeline_push_with_object(self):
        class Anything():
            def __init__(self):
                pass

            def __call__(self):
                return 42

        p = Pipeline([Anything()])
        p.lock()
        result = p.push()
        assert result is 42

    def test_pipeline_process_single_thread(self):
        def sum1(x):
            return x + 1

        p = Pipeline([sum1])
        p.lock()
        result = p.process([0])
        assert sum(result) == 1

        p = Pipeline([sum1, sum1, sum1])
        p.lock()
        result = p.process([0])
        assert sum(result) == 3

    def test_pipeline_process_single_thread_no_args_no_return(self):
        def void():
            pass

        p = Pipeline([void])
        p.lock()
        result = p.process(range(2))
        assert result == [None, None]

    def test_pipeline_process_single_thread_with_args_no_return(self):
        def void(*a, **k):
            pass

        p = Pipeline([void])
        p.lock()
        result = p.process(range(2))
        assert result == [None, None]

    def test_pipeline_process_single_thread_with_args_and_return(self):
        def identity(x):
            return x

        p = Pipeline([identity])
        p.lock()
        result = p.process(range(10))
        assert result == list(range(10))

    def test_pipeline_process_single_thread_with_other_pipeline(self):
        def identity(x):
            return x

        def one():
            return 1

        def sum1(x):
            return x + 1

        p = Pipeline([identity])
        p.lock()

        q = Pipeline([one, p, sum1])
        q.lock()
        result = sum(q.process(range(10)))
        assert result == 20

        p = Pipeline([identity, sum1])
        p.lock()

        q = Pipeline([one, p])
        q.lock()
        result = sum(q.process(range(10)))
        assert result == 20

    def test_pipeline_process_multi_thread_with_no_args_but_return(self):
        def one():
            return 1

        p = Pipeline([one], parallel=True, workers=6)
        p.lock()
        result = sum(p.process(range(1000)))
        assert result == 1000

    def test_pipeline_process_multi_thread_with_args_and_return(self):
        def identity(x):
            return x

        p = Pipeline([identity], parallel=True, workers=6)
        p.lock()
        result = p.process(range(1000))
        result.sort()
        assert result == list(range(1000))

    def test_pipeline_process_multi_thread_with_other_single_thread_pipeline(self):
        def identity(x):
            return x

        def one():
            return 1

        def sum1(x):
            return x + 1

        p = Pipeline([identity])
        p.lock()

        q = Pipeline([one, p, sum1], parallel=True, workers=6)
        q.lock()
        result = sum(q.process(range(10)))
        assert result == 20

        p = Pipeline([identity])
        p.lock()

        q = Pipeline([one, p, sum1], parallel=True, workers=6)
        q.lock()
        result = sum(q.process(range(10)))
        assert result == 20

    def test_pipeline_process_multi_thread_with_other_multi_thread_pipeline(self):
        def sum_set(x):
            return sum(x)

        def minus1(x):
            return x - 1

        def identity(x):
            return x

        def get_hundred_of(x):
            return [x] * 100

        # will spawn (2 ** 3) + 2 threads
        p = Pipeline([minus1], parallel=True, workers=3)
        p.lock()

        q = Pipeline([get_hundred_of, p, sum_set], parallel=True, workers=2)
        q.lock()
        result = sum(q.process([1]*100))
        assert result == 0


if __name__ == "__main__":
    unittest.main()
