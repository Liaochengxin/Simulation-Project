#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"
#include "G4EmStandardPhysics_option4.hh"
#include "G4VModularPhysicsList.hh"

#include "DetectorConstruction.hh"
#include "ActionInitialization.hh"

#include <string>

namespace {
G4String OutputFileNameFromMacro(int argc, char** argv) {
    if (argc <= 1) {
        return "SimulationResults_nt_DoseData.csv";
    }

    std::string macroName = argv[1];
    if (macroName.find("gamma") != std::string::npos) {
        return "gamma_results_nt_DoseData.csv";
    }
    if (macroName.find("proton") != std::string::npos) {
        return "proton_results_nt_DoseData.csv";
    }
    return "SimulationResults_nt_DoseData.csv";
}
}

int main(int argc, char** argv) {
    // 初始化多线程或单线程运行管理器
    auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);

    // 1. 注册探测器构造 (包含人体尺寸 260x120x500 mm 和 10微米细胞)
    runManager->SetUserInitialization(new DetectorConstruction());

    // 2. 注册电磁物理。第一问只比较 gamma/proton 的沉积、LET 和 Bragg peak。
    G4VModularPhysicsList* physicsList = new G4VModularPhysicsList;
    physicsList->RegisterPhysics(new G4EmStandardPhysics_option4(0));
    physicsList->SetVerboseLevel(0);
    runManager->SetUserInitialization(physicsList);

    // 3. 注册用户行为 (产生射线、记录数据)
    runManager->SetUserInitialization(new ActionInitialization(OutputFileNameFromMacro(argc, argv)));

    G4UImanager* UImanager = G4UImanager::GetUIpointer();

    if (argc != 1) { 
        // 批处理模式
        G4String command = "/control/execute ";
        G4String fileName = argv[1];
        UImanager->ApplyCommand(command + fileName);
    } else { 
        // 图形界面模式
        G4VisManager* visManager = new G4VisExecutive;
        visManager->Initialize();
        G4UIExecutive* ui = new G4UIExecutive(argc, argv);
        UImanager->ApplyCommand("/control/execute vis.mac");
        ui->SessionStart();
        delete ui;
        delete visManager;
    }

    delete runManager;
    return 0;
}
