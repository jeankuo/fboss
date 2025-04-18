/*
 *  Copyright (c) 2004-present, Facebook, Inc.
 *  All rights reserved.
 *
 *  This source code is licensed under the BSD-style license found in the
 *  LICENSE file in the root directory of this source tree. An additional grant
 *  of patent rights can be found in the PATENTS file in the same directory.
 *
 */
#pragma once
#include <memory>

namespace facebook::fboss {
class StateDelta;
class SwitchState;
class EcmpGroupConsolidator {
 public:
  std::shared_ptr<SwitchState> consolidate(const StateDelta& delta);

 private:
};
} // namespace facebook::fboss
