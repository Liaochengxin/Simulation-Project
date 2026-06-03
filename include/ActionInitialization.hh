#ifndef ActionInitialization_h
#define ActionInitialization_h 1
#include "G4VUserActionInitialization.hh"
#include "globals.hh"

class ActionInitialization : public G4VUserActionInitialization {
public:
    explicit ActionInitialization(const G4String& outputFileName = "SimulationResults_nt_DoseData.csv");
    ~ActionInitialization() override = default;
    void BuildForMaster() const override;
    void Build() const override;

private:
    G4String fOutputFileName;
};
#endif
