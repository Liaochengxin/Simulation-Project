#include "DetectorConstruction.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4Sphere.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"
#include "G4Color.hh"

G4VPhysicalVolume* DetectorConstruction::Construct() {
    G4NistManager* nist = G4NistManager::Instance();
    G4Material* tissue = nist->FindOrBuildMaterial("G4_TISSUE_SOFT_ICRP");
    G4Material* air = nist->FindOrBuildMaterial("G4_AIR");

    // --- 1. World (世界容器) ---
    G4Box* solidWorld = new G4Box("World", 1*m, 1*m, 2*m);
    G4LogicalVolume* logicWorld = new G4LogicalVolume(solidWorld, air, "World");
    logicWorld->SetVisAttributes(G4VisAttributes::GetInvisible());
    G4VPhysicalVolume* physWorld = new G4PVPlacement(0, G4ThreeVector(), logicWorld, "World", 0, false, 0);

    // --- 2. 躯干 (实心长方体 - 绿色) ---
    // 尺寸: 260mm(X) x 120mm(Y) x 500mm(Z) -> 半宽值需除以2
    G4Box* solidTorso = new G4Box("Torso", 130*mm, 60*mm, 250*mm);
    G4LogicalVolume* logicTorso = new G4LogicalVolume(solidTorso, tissue, "Torso");
    auto torsoVis = new G4VisAttributes(G4Color(0.0, 0.85, 0.25, 0.65));
    torsoVis->SetForceWireframe(true);
    torsoVis->SetForceAuxEdgeVisible(true);
    logicTorso->SetVisAttributes(torsoVis);
    new G4PVPlacement(0, G4ThreeVector(0,0,0), logicTorso, "Torso", logicWorld, false, 0);

    // --- 3. 头部 (实心球体 - 黄色) ---
    // 直径 180mm -> 半径 90mm
    G4Sphere* solidHead = new G4Sphere("Head", 0, 90*mm, 0, 360*deg, 0, 180*deg);
    G4LogicalVolume* logicHead = new G4LogicalVolume(solidHead, tissue, "Head");
    auto headVis = new G4VisAttributes(G4Color(1.0, 0.85, 0.10, 0.55));
    headVis->SetForceSolid(true);
    headVis->SetForceAuxEdgeVisible(true);
    logicHead->SetVisAttributes(headVis);
    // 位置: 躯干顶部(250) + 颈部高(90) + 头部半径(90) = 430mm
    new G4PVPlacement(0, G4ThreeVector(0, 0, 430*mm), logicHead, "Head", logicWorld, false, 0);

    // --- 4. 颈部 (实心圆柱 - 橙色) ---
    // 直径 100mm -> 半径 50mm, 高 90mm -> 半高 45mm
    G4Tubs* solidNeck = new G4Tubs("Neck", 0, 50*mm, 45*mm, 0, 360*deg);
    G4LogicalVolume* logicNeck = new G4LogicalVolume(solidNeck, tissue, "Neck");
    auto neckVis = new G4VisAttributes(G4Color(1.0, 0.45, 0.05, 0.55));
    neckVis->SetForceSolid(true);
    neckVis->SetForceAuxEdgeVisible(true);
    logicNeck->SetVisAttributes(neckVis);
    // 位置: 躯干顶部(250) + 颈部半高(45) = 295mm
    new G4PVPlacement(0, G4ThreeVector(0, 0, 295*mm), logicNeck, "Neck", logicWorld, false, 0);

    // --- 5. 腿部 (实心圆柱 - 蓝色) ---
    // 直径 110mm -> 半径 55mm, 高 820mm -> 半高 410mm
    G4Tubs* solidLeg = new G4Tubs("Leg", 0, 55*mm, 410*mm, 0, 360*deg);
    G4LogicalVolume* logicLeg = new G4LogicalVolume(solidLeg, tissue, "Leg");
    auto legVis = new G4VisAttributes(G4Color(0.0, 0.45, 1.0, 0.55));
    legVis->SetForceSolid(true);
    legVis->SetForceAuxEdgeVisible(true);
    logicLeg->SetVisAttributes(legVis);
    // 左右位置: 110mm直径，左右中心距应为 110mm (即X = ±55mm)
    // 高度位置: 躯干底部(-250) - 腿部半高(410) = -660mm
    new G4PVPlacement(0, G4ThreeVector(-55*mm, 0, -660*mm), logicLeg, "LegL", logicWorld, false, 0);
    new G4PVPlacement(0, G4ThreeVector(55*mm, 0, -660*mm), logicLeg, "LegR", logicWorld, false, 0);

    // --- 6. 癌症部分 (实心长方体 - 红色) ---
    // 尺寸: 长(X) 2cm, 宽(Y) 1cm, 高(Z) 3cm -> 半宽 1cm, 0.5cm, 1.5cm
    G4Box* solidTumor = new G4Box("Tumor", 1.0*cm, 0.5*cm, 1.5*cm);
    G4LogicalVolume* logicTumor = new G4LogicalVolume(solidTumor, tissue, "Tumor");
    auto tumorVis = new G4VisAttributes(G4Color(1.0, 0.0, 0.0, 1.0));
    tumorVis->SetForceSolid(true);
    tumorVis->SetForceAuxEdgeVisible(true);
    logicTumor->SetVisAttributes(tumorVis);

    // 坐标计算 (相对于躯干中心):
    // Z轴：距离顶端 25cm，躯干总高 50cm，所以 Z = 0
    // X轴：躯干半宽 130mm, 距离边缘 5cm(50mm)，所以 X = 130 - 50 - 肿瘤半宽(10) = 70mm
    // 注意：放置在 logicTorso 内部，作为子体积
    new G4PVPlacement(0, G4ThreeVector(70*mm, 0, 0), logicTumor, "Tumor", logicTorso, false, 0);

    return physWorld;
}
