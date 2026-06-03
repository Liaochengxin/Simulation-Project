#include "SteppingAction.hh"
#include "RunAction.hh"
#include "G4Step.hh"
#include "G4Event.hh"
#include "G4EventManager.hh"
#include "G4LogicalVolume.hh"
#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"

namespace {
G4String ClassifyRegion(const G4String& volumeName) {
    if (volumeName == "Tumor") {
        return "Cancer";
    }

    if (volumeName == "Torso" || volumeName == "Head" || volumeName == "Neck" ||
        volumeName == "LegL" || volumeName == "LegR") {
        return "Normal";
    }

    return "";
}
}

void SteppingAction::UserSteppingAction(const G4Step* step) {
    G4double edep = step->GetTotalEnergyDeposit();
    if (edep <= 0.) return; // 如果没有能量沉积则跳过

    G4double stepLength = step->GetStepLength();
    if (stepLength <= 0.) return;

    auto preStep = step->GetPreStepPoint();
    auto physVolume = preStep->GetPhysicalVolume();
    if (!physVolume) return;

    G4String particleName = step->GetTrack()->GetDefinition()->GetParticleName();
    G4String volName = physVolume->GetName();
    G4String region = ClassifyRegion(volName);
    if (region.empty()) return;

    auto logicalVolume = physVolume->GetLogicalVolume();
    auto material = logicalVolume->GetMaterial();
    G4double density = material->GetDensity();

    auto track = step->GetTrack();
    auto position = 0.5 * (preStep->GetPosition() + step->GetPostStepPoint()->GetPosition());
    auto event = G4EventManager::GetEventManager()->GetConstCurrentEvent();

    // The beam macros enter from x = +160 mm, so depth is measured along -X.
    G4double depth = 160.*mm - position.x();
    G4double let = edep / stepLength;
    // Dose = energy / (step_length × density) = energy / local_mass
    G4double localMass = stepLength * density;
    G4double dose = edep / localMass;

    G4String incidentParticle = track->GetParticleDefinition()->GetParticleName();
    if (track->GetParentID() != 0 && event && event->GetNumberOfPrimaryVertex() > 0) {
        auto primary = event->GetPrimaryVertex(0)->GetPrimary(0);
        if (primary) {
            incidentParticle = primary->GetParticleDefinition()->GetParticleName();
        }
    }

    RunAction::WriteDoseRow(region,
                            volName,
                            particleName,
                            incidentParticle,
                            edep / MeV,
                            stepLength / mm,
                            let / (MeV/mm),
                            dose / gray,
                            position.x() / mm,
                            position.y() / mm,
                            position.z() / mm,
                            depth / mm,
                            event ? event->GetEventID() : -1,
                            track->GetTrackID(),
                            track->GetParentID(),
                            track->GetParticleDefinition()->GetPDGEncoding());
}
