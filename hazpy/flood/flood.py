from ..common.classes import Base
from .agriculture import Agriculture
from .direct_social_losses import DirectSocialLosses
from .essential_facilities import EssentialFacilities
from .general_building_stock import GeneralBuildingStock
from .indirect_economic_loss import IndirectEconomicLoss
from .transportation_systems import TransportationSystems
from .udf import UDF
from .utility_systems import UtilitySystems
from .vehicles import Vehicles
from .what_if import WhatIf


class Flood(Base):
    """
    Intialize a flood module instance

    Keyword arguments: \n

    """

    def __init__(self):
        super().__init__()

        self.analysis = Analysis()
        self.UDF = UDF()


class Analysis():
    def __init__(self):

        self.agriculture = Agriculture()
        self.directSocialLosses = DirectSocialLosses()
        self.essentialFacilities = EssentialFacilities()
        self.generalBuildingStock = GeneralBuildingStock()
        self.indirectEconomicLoss = IndirectEconomicLoss()
        self.transportationSystems = TransportationSystems()
        self.UDF = UDF()
        self.utilitySystems = UtilitySystems()
        self.vehicles = Vehicles()
        self.whatIf = WhatIf()
