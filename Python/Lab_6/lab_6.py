#1 вариант

class Building:
    def __init__(self, area, cost_per_meter, residents):
        self.area = area
        self.cost_per_meter = cost_per_meter
        self.residents = residents

    def calculate_cost(self):
        return self.area * self.cost_per_meter

class Village_houe(Building):
    def __init__(self, area, cost_per_meter, residents, garden_cost):
        super().__init__(area, cost_per_meter, residents)
        self.garden_cost = garden_cost

    def cost_per_resident_ratio(self):
        if self.residents > 0:
            return (super().calculate_cost() + self.garden_cost) / self.residents
        else:
            return float('inf')

class City_apartment(Building):
    def __init__(self, area, cost_per_meter, residents, parking_cost):
        super().__init__(area, cost_per_meter, residents)
        self.parking_cost = parking_cost

    def cost_per_resident_ratio(self):
        if self.residents > 0:
            return (super().calculate_cost() + self.parking_cost) / self.residents
        else:
            return float('inf')
