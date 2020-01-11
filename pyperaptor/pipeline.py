from typing import Callable, Generator
from types import FunctionType
import logging
import copy

import concurrent
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
import functools


class PipelineNodeError(Exception):
    pass


class InvalidNodeOperation(Exception):
    pass


class Device():
    def __init__(self, name: str, number : int = 1):
        self.name = name
        assert number > 0, Exception("Remember Devices are wrappers for BoundedSemaphores. You cannot have less than 1")
        assert type(number) == int, Exception("Device number is quantity, must be integer not %s" % type(number))
        self.__sem__ = BoundedSemaphore(number)

    def __repr__(self):
        return "name: {}, locked: {}".format(self.name, self.__lock__.locked)
    
    def get(self):
        self.__sem__.acquire()
    
    def release(self):
        self.__sem__.release()

class Node():
    def __init__(
            self,
            clb: Callable,
            dev: Device = None,
            hold: bool = False,
            keyName=None,
            **refer):
        self._fn = clb
        self._dev = dev
        self._refer = refer
        self._hold = hold
        if hold:
            assert keyName, PipelineNodeError(
                "Invalid keyName for Node %s" %
                str(clb))
        self._key = keyName

    def __add__(self, node):
        if isinstance(node, Pipeline):
            node.add(0, self)
            return node
        elif isinstance(node, Node) or hasattr(node, "__call__"):
            pipe = Pipeline()
            pipe.add(self)
            pipe.add(node)
            return pipe
        else:
            raise InvalidNodeOperation(
                "Trying to add {} and {} is an invalid node operation".format(
                    self, node))

    def get_fn(self):
        return self._fn

    def get_hold(self):
        return self._hold

    def get_key(self):
        return self._key

    def get_refer(self):
        return self._refer

    def __str__(self):
        return "Node(Function: {}, Device: {},  Hold: {})".format(
            self._fn, self._dev, self._hold)
        
    def has_device(self):
        return self._dev is not None
    
    def obtain_device(self):
        if self.has_device():
            self._dev.get()

    def return_device(self):
        if self.has_device():
            self._dev.release()

class LockedPipelineError(Exception):
    pass


class UnlockedPipelineError(Exception):
    pass


class ProcessNoGeneratorError(Exception):
    pass


class PipelineUnsupportedReferInParallelMode(Exception):
    pass


class Pipeline():
    def __init__(self, functions_list: list = None,
                 parallel: bool = False,
                 workers: int = 6,
                 executor: concurrent.futures.Executor = ThreadPoolExecutor):
        self.__tasks__ = []
        self.holding = {}
        self.__locked__ = False
        self.__valid__ = False
        self.__parallel__ = parallel
        self.set_parallel(
            parallel=parallel,
            workers=workers,
            executor=executor)
        if functions_list is not None and len(functions_list) > 0:
             for i in functions_list:
                 self.add(Node(i))


    def set_parallel(
            self,
            parallel: bool = False,
            workers: int = 6,
            executor: concurrent.futures.Executor = ThreadPoolExecutor):
        if parallel:
            self.__max_workers__ = workers
            self.__executor__ = executor
            self.process = self.__parallel_process
        else:
            self.__max_workers__ = 1
            self.__executor__ = None
            self.process = self.__single_process

    def is_parallel(self):
        return self.__parallel__

    def copy(self):
        return copy.deepcopy(self)

    def __call__(self, args):
        return self.push(args)

    def __repr__(self):
        return "Pipeline:\"parallel: {}, workers: {}, executor: {}, steps: [{}]\"".format(
            self.__parallel__, self.__max_workers__, self.__executor__, [
                str(n) for n in self.__tasks__])

    def __str__(self):
        return "Pipeline:\"parallel: {}, workers: {}, executor: {}, # steps: {}\"".format(
            self.__parallel__, self.__max_workers__, self.__executor__, len(self.__tasks__))

    def __iadd__(self, node):
        if isinstance(node, Pipeline):
            for n in node.__tasks__:
                self.__tasks__.append(n)
        else:
            self.add(node)
        return self

    def __add__(self, node):
        if isinstance(node, Pipeline):
            for n in node.__tasks__:
                self.__tasks__.append(n)
        else:
            self.add(node)
        return self

    def add(self, node: Callable, pos: int = None):
        if not isinstance(node, Node) and not isinstance(node, Pipeline):
            node = Node(node)

        if not self.__locked__:
            if pos:
                self.__tasks__.insert(pos, node)
            else:
                self.__tasks__.append(node)
        else:
            raise LockedPipelineError

    def isLocked(self):
        return self.__locked__

    def lock(self):
        self.__validate__()
        self.__locked__ = True

    def __validate__(self):
        if self.__parallel__:
            for n in self.__tasks__:
                if len(n.get_refer().keys()) > 0:
                    raise PipelineUnsupportedReferInParallelMode(
                        "Node {} cannot use REFER because this Pipeline is in parallel mode.".format(
                            n.get_fn()))

    def unlock(self):
        if self.isLocked():
            logger = logging.getLogger("Pipeline")
            logger.log(
                logging.CRITICAL,
                "Unlocking pipline after being lock. This should not happen")

        self.__locked__ = False

    def hold(self, k, v):
        self.holding[k] = v

    def retrieve(self, k):
        return self.holding[k]

    def push(self, i=None, start=0):
        if not self.isLocked():
            raise UnlockedPipelineError(
                "Pipeline must be locked before execution.")

        for c in range(start, len(self.__tasks__)):
            n = self.__tasks__[c]
            f = n.get_fn()

            h = n.get_hold()
            k = n.get_key()
            r = n.get_refer()
            try:
                if self.is_parallel() and isinstance(n, Node) and n.has_device():
                    n.obtain_device()
                if isinstance(i, type(None)):
                    i = f()
                elif isinstance(i, tuple):
                    if f.__code__.co_argcount == 1:
                        if r is None:
                            i = f(i)
                        else:
                            i = f(i, *r.values())
                    else:
                        if r is None:
                            i = f(*i)
                        else:
                            i = f(*i, *r.values())
                else:
                    if r is None or len(r) == 0:
                        i = f(i)
                    else:
                        v = [self.holding[ik] for ik in list(*r.values())]
                        i = f(i, *v)

            except Exception as e:
                raise e

            finally:
                if self.is_parallel() and isinstance(n, Node) and n.has_device():
                    n.return_device()

            if h:
                self.hold(k, i)

        return i

    def __single_process(self, input_iterable=None):
        results = []
        if input_iterable is None:
            g: Callable = self.__tasks__[0].get_fn()
            assert isinstance(g, FunctionType) or \
                   isinstance(g, Generator), \
                   ProcessNoGeneratorError(
                       "{} require a generator at first step for {}.process() but received {}".format(
                        self, self, type(g))
                    )

            if isinstance(g, FunctionType):
                for i in g():
                    i = self.push(i, start=1)
                    results.append(i)
            elif isinstance(g, Generator):
                for i in g:
                    i = self.push(i, start=1)
                    results.append(i)
            else:
                raise ProcessNoGeneratorError(
                    "{} is no function for generator nor a generator itself".format(g))
        else:
            for i in input_iterable:
                i = self.push(i)
                results.append(i)

        return results

    def __parallel_process(self, input_iterable=None):
        results = []
        futures = []
        with self.__executor__(max_workers=self.__max_workers__) as executor:
            if input_iterable is None:
                g: Callable = self.__tasks__[0].get_fn()
                assert isinstance(
                    g, FunctionType) or isinstance(
                        g, Generator), ProcessNoGeneratorError(
                            "{} require a generator at first" +
                            " step for process() but received {}".format(
                                self, type(g)))

                if isinstance(g, FunctionType):
                    for i in g():
                        futures.append(
                            executor.submit(
                                functools.partial(
                                    self.push, i, 1)))
                elif isinstance(g, Generator):
                    for i in g:
                        futures.append(
                            executor.submit(
                                functools.partial(
                                    self.push, i, 1)))
                else:
                    raise ProcessNoGeneratorError(
                        "{} is no function for generator nor a generator itself".format(g))
            else:
                for i in input_iterable:
                    futures.append(
                        executor.submit(
                            functools.partial(self.push, i)
                        ))

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        return results
