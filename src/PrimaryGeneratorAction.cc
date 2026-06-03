#include "PrimaryGeneratorAction.hh"
#include "G4GeneralParticleSource.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction() {
    fParticleSource = new G4GeneralParticleSource();
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
    delete fParticleSource;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
    fParticleSource->GeneratePrimaryVertex(event);
}
