from models.materials import GW2Price, BaseMaterials
from enum import Enum
from dataclasses import dataclass
from typing import Dict

class Profession(Enum):
    HUNTSMAN = "Huntsman"
    WEAPONSMITH = "Weaponsmith"
    ARTIFICER = "Artificer"

class WeaponType(Enum):
    AXE = "Restored Boreal Axe"
    DAGGER = "Restored Boreal Dagger"
    MACE = "Restored Boreal Mace"
    PISTOL = "Restored Boreal Pistol"
    SCEPTER = "Restored Boreal Scepter"
    SWORD = "Restored Boreal Sword"
    FOCUS = "Restored Boreal Focus"
    SHIELD = "Restored Boreal Shield"
    TORCH = "Restored Boreal Torch"
    WARHORN = "Restored Boreal Warhorn"
    GREATSWORD = "Restored Boreal Greatsword"
    HAMMER = "Restored Boreal Hammer"
    LONGBOW = "Restored Boreal Longbow"
    RIFLE = "Restored Boreal Rifle"
    SHORTBOW = "Restored Boreal Short Bow"
    STAFF = "Restored Boreal Staff"
    
    @property
    def profession(self) -> 'Profession':
        profession_map = {
            # Huntsman
            WeaponType.LONGBOW: Profession.HUNTSMAN,
            WeaponType.SHORTBOW: Profession.HUNTSMAN,
            WeaponType.RIFLE: Profession.HUNTSMAN,
            WeaponType.WARHORN: Profession.HUNTSMAN,
            WeaponType.TORCH: Profession.HUNTSMAN,
            WeaponType.PISTOL: Profession.HUNTSMAN,
            # Weaponsmith
            WeaponType.AXE: Profession.WEAPONSMITH,
            WeaponType.SWORD: Profession.WEAPONSMITH,
            WeaponType.MACE: Profession.WEAPONSMITH,
            WeaponType.GREATSWORD: Profession.WEAPONSMITH,
            WeaponType.HAMMER: Profession.WEAPONSMITH,
            WeaponType.SHIELD: Profession.WEAPONSMITH,
            WeaponType.DAGGER: Profession.WEAPONSMITH,
            # Artificer
            WeaponType.SCEPTER: Profession.ARTIFICER,
            WeaponType.FOCUS: Profession.ARTIFICER,
            WeaponType.STAFF: Profession.ARTIFICER,
        }
        return profession_map[self]

@dataclass
class ComponentCost:
    name: str
    cost: GW2Price
    materials: Dict[str, int]

@dataclass
class WeaponRecipe:
    name: str
    ori_ore_count: int
    ancient_wood_count: int
    leather_count: int = 0
    weapon_type: WeaponType = None

    def __post_init__(self):
        if isinstance(self.name, WeaponType):
            self.weapon_type = self.name
            self.name = self.name.value

    def get_components(self) -> Dict[str, Dict[str, int]]:
        components = {
            "Berserker's Orichalcum Imbued Inscription": {}
        }
        
        if self.ori_ore_count > 0:
            if self.weapon_type == WeaponType.AXE:
                components["Orichalcum Axe Blade"] = {"ori_ore": 6}
                components["Ancient Haft"] = {"ancient_wood": 3}
            elif self.weapon_type == WeaponType.DAGGER:
                components["Orichalcum Dagger Blade"] = {"ori_ore": 4}
                components["Ancient Hilt"] = {"ancient_wood": 3}
            elif self.weapon_type == WeaponType.SWORD:
                components["Orichalcum Sword Blade"] = {"ori_ore": 4}
                components["Ancient Hilt"] = {"ancient_wood": 3}
            elif self.weapon_type == WeaponType.MACE:
                components["Orichalcum Mace Head"] = {"ori_ore": 6}
                components["Ancient Haft"] = {"ancient_wood": 3}
            elif self.weapon_type == WeaponType.SHIELD:
                components["Orichalcum Shield Boss"] = {"ori_ore": 4}
                components["Ancient Shield Backing"] = {"ancient_wood": 6}
            elif self.weapon_type == WeaponType.WARHORN:
                components["Orichalcum Horn"] = {"ori_ore": 4}
                components["Orichalcum Warhorn Mouthpiece"] = {"ori_ore": 2}
            elif self.weapon_type == WeaponType.GREATSWORD:
                components["Orichalcum Greatsword Blade"] = {"ori_ore": 8}
                components["Ancient Greatsword Hilt"] = {"ancient_wood": 6}
            elif self.weapon_type == WeaponType.HAMMER:
                components["Orichalcum Hammer Head"] = {"ori_ore": 8}
                components["Ancient Haft"] = {"ancient_wood": 6}
            elif self.weapon_type == WeaponType.RIFLE:
                components["Orichalcum Rifle Barrel"] = {"ori_ore": 6}
                components["Ancient Rifle Stock"] = {"ancient_wood": 6}
            elif self.weapon_type == WeaponType.PISTOL:
                components["Orichalcum Pistol Barrel"] = {"ori_ore": 4}
                components["Ancient Pistol Frame"] = {"ancient_wood": 3}
            elif self.weapon_type == WeaponType.TORCH:
                components["Orichalcum Torch Head"] = {"ori_ore": 4}
                components["Ancient Torch Handle"] = {"ancient_wood": 3}
        else:
            if self.weapon_type == WeaponType.SCEPTER:
                components["Ancient Scepter Core"] = {"ancient_wood": 3}
                components["Ancient Scepter Rod"] = {"ancient_wood": 3}
            elif self.weapon_type == WeaponType.FOCUS:
                components["Ancient Focus Casing"] = {"ancient_wood": 3}
                components["Ancient Focus Core"] = {"ancient_wood": 3}
            elif self.weapon_type == WeaponType.STAFF:
                components["Ancient Staff Head"] = {"ancient_wood": 3}
                components["Ancient Staff Shaft"] = {"ancient_wood": 6}
            elif self.weapon_type == WeaponType.LONGBOW:
                components["Ancient Longbow Stave"] = {"ancient_wood": 3}
                components["Hardened String"] = {"leather": 3}
            elif self.weapon_type == WeaponType.SHORTBOW:
                components["Ancient Short-Bow Stave"] = {"ancient_wood": 3}
                components["Hardened String"] = {"leather": 3}
        
        return components

class CraftingCalculator:
    def __init__(self):
        self.recipes = {
            WeaponType.AXE: WeaponRecipe(WeaponType.AXE, 12, 6),
            WeaponType.DAGGER: WeaponRecipe(WeaponType.DAGGER, 10, 0),
            WeaponType.MACE: WeaponRecipe(WeaponType.MACE, 12, 6),
            WeaponType.PISTOL: WeaponRecipe(WeaponType.PISTOL, 6, 6),
            WeaponType.SCEPTER: WeaponRecipe(WeaponType.SCEPTER, 0, 15),
            WeaponType.SWORD: WeaponRecipe(WeaponType.SWORD, 12, 0),
            WeaponType.FOCUS: WeaponRecipe(WeaponType.FOCUS, 0, 15),
            WeaponType.SHIELD: WeaponRecipe(WeaponType.SHIELD, 8, 0),
            WeaponType.TORCH: WeaponRecipe(WeaponType.TORCH, 4, 6),
            WeaponType.WARHORN: WeaponRecipe(WeaponType.WARHORN, 4, 6),
            WeaponType.GREATSWORD: WeaponRecipe(WeaponType.GREATSWORD, 12, 0),
            WeaponType.HAMMER: WeaponRecipe(WeaponType.HAMMER, 6, 6),
            WeaponType.LONGBOW: WeaponRecipe(WeaponType.LONGBOW, 0, 12, 9),
            WeaponType.RIFLE: WeaponRecipe(WeaponType.RIFLE, 6, 9),
            WeaponType.SHORTBOW: WeaponRecipe(WeaponType.SHORTBOW, 0, 12, 9),
            WeaponType.STAFF: WeaponRecipe(WeaponType.STAFF, 0, 18)
        }
    
    def calculate_cost(self, recipe: WeaponRecipe, materials: BaseMaterials) -> GW2Price:
        total_copper = materials.inscription_price.to_copper()
        total_copper += (materials.ori_ore_price.to_copper() * recipe.ori_ore_count)
        total_copper += (materials.ancient_wood_price.to_copper() * recipe.ancient_wood_count)
        total_copper += (materials.leather_price.to_copper() * recipe.leather_count)
        
        return GW2Price.from_copper(total_copper)

    def calculate_detailed_cost(self, recipe: WeaponRecipe, materials: BaseMaterials) -> Dict[str, 'ComponentCost']:
        components = {}
        weapon_name = recipe.name
        
        # Inscription
        components["Berserker's Orichalcum Imbued Inscription"] = ComponentCost(
            name="Berserker's Orichalcum Imbued Inscription",
            cost=materials.inscription_price,
            materials={}
        )
        
        # Spezifische Komponenten je nach Waffentyp
        if weapon_name == "Restored Boreal Axe":
            if recipe.ori_ore_count > 0:
                components["Orichalcum Axe Blade"] = ComponentCost(
                    name="Orichalcum Axe Blade",
                    cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                    materials={"ori_ore": 6}
                )
            if recipe.ancient_wood_count > 0:
                components["Small Ancient Haft"] = ComponentCost(
                    name="Small Ancient Haft",
                    cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 6),
                    materials={"ancient_wood": 6}
                )

        elif weapon_name == "Restored Boreal Dagger":
            components["Orichalcum Dagger Blade"] = ComponentCost(
                name="Orichalcum Dagger Blade",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )
            components["Orichalcum Dagger Hilt"] = ComponentCost(
                name="Orichalcum Dagger Hilt",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 4),
                materials={"ori_ore": 4}
            )

        elif weapon_name == "Restored Boreal Mace":
            components["Orichalcum Mace Head"] = ComponentCost(
                name="Orichalcum Mace Head",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )
            components["Small Ancient Haft"] = ComponentCost(
                name="Small Ancient Haft",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 6),
                materials={"ancient_wood": 6}
            )

        elif weapon_name == "Restored Boreal Pistol":
            components["Orichalcum Pistol Barrel"] = ComponentCost(
                name="Orichalcum Pistol Barrel",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )
            components["Ancient Pistol Frame"] = ComponentCost(
                name="Ancient Pistol Frame",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 6),
                materials={"ancient_wood": 6}
            )

        elif weapon_name == "Restored Boreal Scepter":
            components["Ancient Scepter Core"] = ComponentCost(
                name="Ancient Scepter Core",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 6),
                materials={"ancient_wood": 6}
            )
            components["Ancient Scepter Rod"] = ComponentCost(
                name="Ancient Scepter Rod",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 9),
                materials={"ancient_wood": 9}
            )

        elif weapon_name == "Restored Boreal Sword":
            components["Orichalcum Sword Blade"] = ComponentCost(
                name="Orichalcum Sword Blade",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )
            components["Orichalcum Sword Hilt"] = ComponentCost(
                name="Orichalcum Sword Hilt",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )

        elif weapon_name == "Restored Boreal Focus":
            components["Ancient Focus Core"] = ComponentCost(
                name="Ancient Focus Core",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 6),
                materials={"ancient_wood": 6}
            )
            components["Ancient Focus Casing"] = ComponentCost(
                name="Ancient Focus Casing",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 9),
                materials={"ancient_wood": 9}
            )

        elif weapon_name == "Restored Boreal Shield":
            components["Ancient Shield Backing"] = ComponentCost(
                name="Ancient Shield Backing",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 4),
                materials={"ori_ore": 4}
            )
            components["Orichalcum Shield Boss"] = ComponentCost(
                name="Orichalcum Shield Boss",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 4),
                materials={"ori_ore": 4}
            )

        elif weapon_name == "Restored Boreal Torch":
            components["Ancient Torch Handle"] = ComponentCost(
                name="Ancient Torch Handle",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 6),
                materials={"ancient_wood": 6}
            )
            components["Orichalcum Torch Head"] = ComponentCost(
                name="Orichalcum Torch Head",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 4),
                materials={"ori_ore": 4}
            )

        elif weapon_name == "Restored Boreal Warhorn":
            components["Orichalcum Horn"] = ComponentCost(
                name="Orichalcum Horn",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 2),
                materials={"ori_ore": 2, "ancient_wood": 6}
            )
            components["Orichalcum Warhorn Mouthpiece"] = ComponentCost(
                name="Orichalcum Warhorn Mouthpiece",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 2),
                materials={"ori_ore": 2}
            )

        elif weapon_name == "Restored Boreal Greatsword":
            components["Orichalcum Greatsword Blade"] = ComponentCost(
                name="Orichalcum Greatsword Blade",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )
            components["Ancient Greatsword Hilt"] = ComponentCost(
                name="Ancient Greatsword Hilt",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )

        elif weapon_name == "Restored Boreal Hammer":
            components["Orichalcum Hammer Head"] = ComponentCost(
                name="Orichalcum Hammer Head",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )
            components["Large Ancient Haft"] = ComponentCost(
                name="Large Ancient Haft",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 6),
                materials={"ancient_wood": 6}
            )

        elif weapon_name == "Restored Boreal Longbow":
            components["Ancient Longbow Stave"] = ComponentCost(
                name="Ancient Longbow Stave",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 12),
                materials={"ancient_wood": 12}
            )
            components["Hardened String"] = ComponentCost(
                name="Hardened String",
                cost=GW2Price.from_copper(materials.leather_price.to_copper() * 9),
                materials={"leather": 9}
            )

        elif weapon_name == "Restored Boreal Rifle":
            components["Orichalcum Rifle Barrel"] = ComponentCost(
                name="Orichalcum Rifle Barrel",
                cost=GW2Price.from_copper(materials.ori_ore_price.to_copper() * 6),
                materials={"ori_ore": 6}
            )
            components["Ancient Rifle Stock"] = ComponentCost(
                name="Ancient Rifle Stock",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 9),
                materials={"ancient_wood": 9}
            )

        elif weapon_name == "Restored Boreal Short Bow":
            components["Ancient Short-Bow Stave"] = ComponentCost(
                name="Ancient Short-Bow Stave",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 12),
                materials={"ancient_wood": 12}
            )
            components["Hardened String"] = ComponentCost(
                name="Hardened String",
                cost=GW2Price.from_copper(materials.leather_price.to_copper() * 9),
                materials={"leather": 9}
            )

        elif weapon_name == "Restored Boreal Staff":
            components["Ancient Staff Head"] = ComponentCost(
                name="Ancient Staff Head",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 6),
                materials={"ancient_wood": 6}
            )
            components["Ancient Staff Shaft"] = ComponentCost(
                name="Ancient Staff Shaft",
                cost=GW2Price.from_copper(materials.ancient_wood_price.to_copper() * 12),
                materials={"ancient_wood": 12}
            )

        return components

    def get_all_recipes(self):
        return self.recipes