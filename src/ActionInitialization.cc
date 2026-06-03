#include "ActionInitialization.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "SteppingAction.hh"

ActionInitialization::ActionInitialization(const G4String& outputFileName)
    : fOutputFileName(outputFileName) {}

void ActionInitialization::BuildForMaster() const {
    SetUserAction(new RunAction(fOutputFileName));
}

void ActionInitialization::Build() const {
    SetUserAction(new PrimaryGeneratorAction());
    SetUserAction(new RunAction(fOutputFileName));
    SetUserAction(new SteppingAction());
}
