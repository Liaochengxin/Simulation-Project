#ifndef RunAction_h
#define RunAction_h 1
#include "G4UserRunAction.hh"
#include "globals.hh"
#include <fstream>
class G4Run;

class RunAction : public G4UserRunAction {
public:
    explicit RunAction(const G4String& outputFileName = "SimulationResults_nt_DoseData.csv");
    ~RunAction() override;
    void BeginOfRunAction(const G4Run*) override;
    void EndOfRunAction(const G4Run*) override;

    static void WriteDoseRow(const G4String& region,
                             const G4String& volumeName,
                             const G4String& particleName,
                             const G4String& incidentParticle,
                             G4double energyDepositMeV,
                             G4double stepLengthMm,
                             G4double letMeVPerMm,
                             G4double doseGy,
                             G4double xMm,
                             G4double yMm,
                             G4double zMm,
                             G4double depthMm,
                             G4int eventID,
                             G4int trackID,
                             G4int parentID,
                             G4int pdgEncoding);

private:
    G4String fOutputFileName;
    std::ofstream fOutput;
    static RunAction* fInstance;
};
#endif
