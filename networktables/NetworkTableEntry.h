#pragma once

#include <string>

namespace nt {

class NetworkTableEntry {
 public:
  double GetDouble(double default_value) const {
    return double_value_set_ ? double_value_ : default_value;
  }

  bool GetBoolean(bool default_value) const {
    return bool_value_set_ ? bool_value_ : default_value;
  }

  std::string GetString(const std::string& default_value) const {
    return string_value_set_ ? string_value_ : default_value;
  }

  void SetDouble(double value) {
    double_value_set_ = true;
    double_value_ = value;
  }

  void SetBoolean(bool value) {
    bool_value_set_ = true;
    bool_value_ = value;
  }

  void SetString(const std::string& value) {
    string_value_set_ = true;
    string_value_ = value;
  }

 private:
  double double_value_ = 0.0;
  bool bool_value_ = false;
  bool double_value_set_ = false;
  bool bool_value_set_ = false;
  std::string string_value_;
  bool string_value_set_ = false;
};

}  // namespace nt
