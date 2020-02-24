import unittest
from unittest import mock
from unittest.mock import Mock
from unittest.mock import patch


def simple_function():
    a = 2
    b = 3
    result = a * b
    print('From simple_function', result)
    return result


def test_simple_function():
    result = simple_function()
    print(result)


@unittest.skip("test test")
@patch('tngsdk.benchmark.tests.test_osm_pdriver.test_data.simple_function')
def test_mock_simple_function(mock_simple_func):
    print(mock_simple_func)
    r = mock_simple_func()
    print(r)
    print(simple_function)
    result = simple_function()
    print(result)
