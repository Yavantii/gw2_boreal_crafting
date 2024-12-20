from dataclasses import dataclass

@dataclass
class GW2Price:
    gold: int
    silver: int
    copper: int
    
    def to_copper(self) -> int:
        return self.gold * 10000 + self.silver * 100 + self.copper
    
    @staticmethod
    def from_copper(copper: int) -> 'GW2Price':
        gold = copper // 10000
        copper = copper % 10000
        silver = copper // 100
        copper = copper % 100
        return GW2Price(gold, silver, copper)

@dataclass
class BaseMaterials:
    inscription_price: GW2Price
    ori_ore_price: GW2Price
    ancient_wood_price: GW2Price
    leather_price: GW2Price