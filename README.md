# PypeRaptor
**Version:**  0.1.3.1 [![Build Status](https://travis-ci.org/fsan/pyperaptor.svg?branch=master)](https://travis-ci.org/fsan/pyperaptor)

PypeRaptor is a library that provides a functional pipeline structure.
Each execution from the pipeline takes an input item from beginning to end and return the result.
The Pipeline may be modified by add operator and expects a Node.
To execute a Pipeline for a single item, user can execute **push** function with item. This execution will pushes the input
through the pipeline calling every function in the way.
To execute several items, user can set an Iterable in **process** function.

A generator can be part of the pipeline, and is recommended to be the first item to when using Pipeline in parallel mode.
When in parallel mode, PypeRaptor provides a Device as in a way to reserve resources and avoid racing conditions among its threads.

For more details and explanation over PypeRaptor goto: [PypeRaptor Doc](https://fsan.github.io/post/pyperaptor/)

## Installation

``` pip install pyperaptor ```

## Quick guide

1. Create Pipeline object
2. Create Node(s) object(s) containing the function to be executed.
3. Lock the Pipeline
4. Execute the pipeline

## Examples

* Simplest example

```python
from pyperaptor import Pipeline, Node

def sum1(x):
    return x + 1

p = Pipeline()
p += Node(sum1)

p.lock()

result = p.push(2)
print(result)

# 3
```

* Using process for multiple inputs

```python
from pyperaptor import Pipeline, Node

def sum1(x):
    return x + 1

def a_generator():
    for x in range(10):
        yield x

p = Pipeline()
p += Node(sum1)

p.lock()

results = p.process(list(a_generator()))
print(results)

# [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

* Simple example using a generator inside the pipeline

```python
from pyperaptor import Pipeline, Node

def sum1(x):
    return x + 1

def a_generator():
    for x in range(10):
        yield x

p = Pipeline()
p += Node(a_generator) + \
     sum1


p.lock()

results = p.process()
print(results)

# [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```
* Using a function list as input for the pipeline

```python
from pyperaptor import Pipeline, Node

def sum1(x):
    return x + 1

def sum2(x):
    return x + 2

def a_generator():
    for x in range(10):
        yield x

p = Pipeline([sum1, sum2])

p.lock()

results = p.process()
print(results)

# [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

* Making a pipeline parallel

```python
from pyperaptor import Pipeline, Node

def sum1(x):
    return x + 1

def a_generator():
    for x in range(10):
        yield x

p = Pipeline(parallel=True, workers=10)
p += Node(a_generator) + \
     sum1

p.lock()

results = p.process()
print(results)

# [6, 5, 1, 10, 9, 3, 7, 2, 8, 4]
```

* Using a Device to avoid racing condition

First, let's see the problem happening:
```python
from pyperaptor import Pipeline, Device, Node

def sum1(x):
    return x + 1

def printer(x):
    print(x, end=" ")
    return x

def a_generator():
    for x in range(10):
        yield x

p = Pipeline(parallel=True, workers=10)
p += Node(sum1) + \
     printer

p.lock()

p.process(list(a_generator()))
# 1 2 3 465 8  7 9 10
```
The above output fails on spacing items because the terminal output is being used by many threads at same time.
To solve this problem let's guarantee that this will not happen

```python
from pyperaptor import Pipeline, Device, Node

def sum1(x):
    return x + 1

def printer(x):
    print(x, end=" ")
    return x

def a_generator():
    for x in range(10):
        yield x
        
TERM = Device("term1")
        
p = Pipeline(parallel=True, workers=10)
p += Node(sum1) + \
     Node(printer, dev=TERM)

p.lock()

p.process(list(a_generator()))
# 1 2 3 4 5 10 7 8 9 6
```


## Other features

* Hold and Refer
In single thread mode, you can refer to another item result if you name it and refer to it with *refer* and *hold* parameter

```python
from pyperaptor import Pipeline, Node

def sum1(x):
    return x + 1

def printer(*x):
    print(*x)
    return x

p = Pipeline()
p += Node(sum1, keyName="sum1_result", hold=True) + \
     Node(printer, refer=["sum1_result"])

p.lock()
p.process(list(range(10)))
# 1 1
# 2 2
# 3 3
# 4 4
# ...

```
The first output for printer comes from the result of sum1 itself and the second output was recovered from *refer* and appended to *args

* Multiple Devices
The Device entity may have multiple resources available. You can treat Device as a semaphore, and pass a number of available resources in the parameter

**Think in Devices as wrappers for Semaphores (because they are)**


```python

ANY_RESOURCE = Device("Some Name", 5)

p = Pipeline()
p += Node(a_function) + \
     Node(other_function, dev=ANY_RESOURCE)

```


## PypeRaptor algebrae

- Pipeline + Node = Pipeline.add(Node)
- Pipeline + Pipeline = Pipeline.add(Pipeline)
- NodeA + NodeB = Pipeline.add(NodeA) + NodeB
