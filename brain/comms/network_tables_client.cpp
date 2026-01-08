#include <networktables/NetworkTableEntry.h>
#include <networktables/NetworkTableInstance.h>

#include <string>

namespace brain {
namespace comms {

class NetworkTablesClient {
 public:
  NetworkTablesClient() : instance_(nt::NetworkTableInstance::GetDefault()) {}

  static constexpr int kTeamNumber = 418;
  static const std::string kDefaultClientName;

  void ConnectTeam(int team, const std::string& client_name = kDefaultClientName) {
    instance_.StopClient();
    instance_.SetIdentity(client_name);
    instance_.SetServerTeam(team);
    instance_.StartClient4(client_name);
  }

  void ConnectDefaultTeam(const std::string& client_name = kDefaultClientName) {
    ConnectTeam(kTeamNumber, client_name);
  }

  void ConnectHost(const std::string& host, const std::string& client_name = kDefaultClientName) {
    instance_.StopClient();
    instance_.SetIdentity(client_name);
    instance_.SetServer(host);
    instance_.StartClient4(client_name);
  }

  bool IsConnected() const { return instance_.IsConnected(); }

  nt::NetworkTableEntry GetEntry(const std::string& entry_name) const {
    return instance_.GetEntry(entry_name);
  }

  double GetDouble(const std::string& entry_name, double default_value = 0.0) const {
    return GetEntry(entry_name).GetDouble(default_value);
  }

  bool GetBoolean(const std::string& entry_name, bool default_value = false) const {
    return GetEntry(entry_name).GetBoolean(default_value);
  }

  std::string GetString(const std::string& entry_name,
                        const std::string& default_value = kEmptyString) const {
    return GetEntry(entry_name).GetString(default_value);
  }

  void PutDouble(const std::string& entry_name, double value) {
    GetEntry(entry_name).SetDouble(value);
  }

  void PutBoolean(const std::string& entry_name, bool value) {
    GetEntry(entry_name).SetBoolean(value);
  }

  void PutString(const std::string& entry_name, const std::string& value) {
    GetEntry(entry_name).SetString(value);
  }

 private:
  static const std::string kEmptyString;
  nt::NetworkTableInstance instance_;
};

const std::string NetworkTablesClient::kDefaultClientName("phadbrain");
const std::string NetworkTablesClient::kEmptyString;

}
}
