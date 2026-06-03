#include "RunAction.hh"
#include <iomanip>

RunAction* RunAction::fInstance = nullptr;

RunAction::RunAction(const G4String& outputFileName)
    : fOutputFileName(outputFileName) {
    fInstance = this;
}

RunAction::~RunAction() {
    if (fInstance == this) {
        fInstance = nullptr;
    }
}

void RunAction::BeginOfRunAction(const G4Run*) {
    fOutput.open(fOutputFileName);
    fOutput << "Region,VolumeName,ParticleName,IncidentParticle,"
            << "EnergyDeposit_MeV,StepLength_mm,LET_MeV_per_mm,Dose_Gy,"
            << "X_mm,Y_mm,Z_mm,Depth_mm,EventID,TrackID,ParentID,PDGEncoding\n";
}

void RunAction::EndOfRunAction(const G4Run*) {
    fOutput.close();
}

void RunAction::WriteDoseRow(const G4String& region,
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
                             G4int pdgEncoding) {
    if (!fInstance || !fInstance->fOutput.is_open()) return;

    auto& out = fInstance->fOutput;
    out << region << ','
        << volumeName << ','
        << particleName << ','
        << incidentParticle << ','
        << std::setprecision(10)
        << energyDepositMeV << ','
        << stepLengthMm << ','
        << letMeVPerMm << ','
        << doseGy << ','
        << xMm << ','
        << yMm << ','
        << zMm << ','
        << depthMm << ','
        << eventID << ','
        << trackID << ','
        << parentID << ','
        << pdgEncoding << '\n';
}
