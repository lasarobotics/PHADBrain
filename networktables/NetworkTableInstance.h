#pragma once

#include <string>

#include "NetworkTableEntry.h"

namespace nt {

class NetworkTableInstance {
 public:
  static NetworkTableInstance GetDefault() {
    static NetworkTableInstance instance;
    return instance;
  }

  void StopClient() {}

  void SetIdentity(const std::string& identity) { identity_ = identity; }

  void SetServerTeam(int team) { server_ = "team:" + std::to_string(team); }

  void SetServer(const std::string& server) { server_ = server; }

  void StartClient4(const std::string&) { connected_ = true; }

  bool IsConnected() const { return connected_; }

  NetworkTableEntry GetEntry(const std::string&) const { return NetworkTableEntry(); }

 private:
  std::string identity_;
  std::string server_;
  bool connected_ = false;
};

}  // namespace nt
