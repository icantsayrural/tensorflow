# Copyright 2018 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for the experimental input pipeline ops."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import parameterized

from tensorflow.contrib.data.python.ops import optimization
from tensorflow.python.data.ops import dataset_ops
from tensorflow.python.framework import errors
from tensorflow.python.platform import test


class OptimizeDatasetTest(test.TestCase, parameterized.TestCase):

  def testAssertSuffix(self):
    dataset = dataset_ops.Dataset.from_tensors(0).apply(
        optimization.assert_next(["Map"])).map(lambda x: x)
    iterator = dataset.make_one_shot_iterator()
    get_next = iterator.get_next()

    with self.test_session() as sess:
      self.assertEqual(0, sess.run(get_next))

  def testAssertSuffixInvalid(self):
    dataset = dataset_ops.Dataset.from_tensors(0).apply(
        optimization.assert_next(["Whoops"])).map(lambda x: x)
    iterator = dataset.make_one_shot_iterator()
    get_next = iterator.get_next()

    with self.test_session() as sess:
      with self.assertRaisesRegexp(
          errors.InvalidArgumentError,
          "Asserted Whoops transformation at offset 0 but encountered "
          "Map transformation instead."):
        sess.run(get_next)

  def testAssertSuffixShort(self):
    dataset = dataset_ops.Dataset.from_tensors(0).apply(
        optimization.assert_next(["Map", "Whoops"])).map(lambda x: x)
    iterator = dataset.make_one_shot_iterator()
    get_next = iterator.get_next()

    with self.test_session() as sess:
      with self.assertRaisesRegexp(
          errors.InvalidArgumentError,
          "Asserted next 2 transformations but encountered only 1."):
        sess.run(get_next)

  def testDefaultOptimizations(self):
    dataset = dataset_ops.Dataset.range(10).apply(
        optimization.assert_next(
            ["Map", "Batch"])).map(lambda x: x * x).batch(10).apply(
                optimization.optimize())
    iterator = dataset.make_one_shot_iterator()
    get_next = iterator.get_next()

    with self.test_session() as sess:
      self.assertAllEqual([x * x for x in range(10)], sess.run(get_next))
      with self.assertRaises(errors.OutOfRangeError):
        sess.run(get_next)

  def testEmptyOptimizations(self):
    dataset = dataset_ops.Dataset.range(10).apply(
        optimization.assert_next(
            ["Map", "Batch"])).map(lambda x: x * x).batch(10).apply(
                optimization.optimize([]))
    iterator = dataset.make_one_shot_iterator()
    get_next = iterator.get_next()

    with self.test_session() as sess:
      self.assertAllEqual([x * x for x in range(10)], sess.run(get_next))
      with self.assertRaises(errors.OutOfRangeError):
        sess.run(get_next)

  def testOptimization(self):
    dataset = dataset_ops.Dataset.range(10).apply(
        optimization.assert_next(
            ["MapAndBatch"])).map(lambda x: x * x).batch(10).apply(
                optimization.optimize(["map_and_batch_fusion"]))
    iterator = dataset.make_one_shot_iterator()
    get_next = iterator.get_next()

    with self.test_session() as sess:
      self.assertAllEqual([x * x for x in range(10)], sess.run(get_next))
      with self.assertRaises(errors.OutOfRangeError):
        sess.run(get_next)


if __name__ == "__main__":
  test.main()
