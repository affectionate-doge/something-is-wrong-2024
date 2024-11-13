from dataclasses import dataclass, asdict, fields, is_dataclass
from typing import List, Type, TypeVar, Union, Dict, Any, Optional, Generic, ClassVar

from data_classes import *

class ElectionDataMap:
    
    election_years: ClassVar[list[int]] = [
        2024,
        2020
    ]
    election_types: ClassVar[dict[str, str]] = {
        "P": "Presidential",
        "S": "Senate",
        "H": "House",
        "G": "Gubernatorial",
    }

    election_states: ClassVar[dict[str, str]] = {
        "AL": "Alabama",
        "AK": "Alaska",
        "AZ": "Arizona",
        "AR": "Arkansas",
        "CA": "California",
        "CO": "Colorado",
        "CT": "Connecticut",
        "DE": "Delaware",
        "FL": "Florida",
        "GA": "Georgia",
        "HI": "Hawaii",
        "ID": "Idaho",
        "IL": "Illinois",
        "IN": "Indiana",
        "IA": "Iowa",
        "KS": "Kansas",
        "KY": "Kentucky",
        "LA": "Louisiana",
        "ME": "Maine",
        "MD": "Maryland",
        "MA": "Massachusetts",
        "MI": "Michigan",
        "MN": "Minnesota",
        "MS": "Mississippi",
        "MO": "Missouri",
        "MT": "Montana",
        "NE": "Nebraska",
        "NV": "Nevada",
        "NH": "New Hampshire",
        "NJ": "New Jersey",
        "NM": "New Mexico",
        "NY": "New York",
        "NC": "North Carolina",
        "ND": "North Dakota",
        "OH": "Ohio",
        "OK": "Oklahoma",
        "OR": "Oregon",
        "PA": "Pennsylvania",
        "RI": "Rhode Island",
        "SC": "South Carolina",
        "SD": "South Dakota",
        "TN": "Tennessee",
        "TX": "Texas",
        "UT": "Utah",
        "VT": "Vermont",
        "VA": "Virginia",
        "WA": "Washington",
        "WV": "West Virginia",
        "WI": "Wisconsin",
        "WY": "Wyoming",
        "DC": "District of Columbia"
    }


@dataclass
class ElectionYearStateCountyDistrictMap(JsonFileData):
    """
    A map of county districts per state and election year.
    Data here is extracted from CNN.
    
    Example structure:
{
    "2024": {                                       // year
        "AL": {                                     // state
            "districts": [ 1, 2, 3, 4, 5, 6, 7 ],   // district numbers
            "counties": [ "Baldwin", "Mobile" ]     // county names
            "county_districts": {                           
                "Baldwin": [ 1 ],                   // county name and districts (not all counties are in only 1 district)
                "Mobile": [ 1, 2 ]
        }
    }
}
    """
    data: Dict[int, Dict[str, Dict[str, Dict[str, List[int]]]]] = field(default_factory=dict)


    

@dataclass
class ElectionDataFullModel(JsonFileData):
    """
    Stores data districts per state and election year. Hierarchal model which contains all data.
    Data here is extracted from CNN.
    
    Example structure:
{
    // year
    "2024": {
        // state
        "AL": {
            // county name
            "Baldwin": {
                // election type
                "P": {
                  "pct_reported": 95.0,
                  "total_votes": 1000,
                  "candidates": {
                    // candidate party
                    "D": {
                        "name": "Kamala Harris",
                        "votes": 40.0,
                        "votes_pct": 40.0
                    },
                    "R": {
                        "name": "Donald Trump",
                        "votes": 585,
                        "votes_pct": 58.5
                    },
                    "timestamp": "2024-11-13T07:55:26.402536"
                  }
                },
                "H": {
                    // district number
                    "1": {
                        "pct_reported": 95.0,
                        "total_votes": 53055,
                        "candidates": {
                            // candidate party
                            "D": {
                                "name": "Tom Holmes",
                                "votes": 17188,
                                "votes_pct": 24.4
                            },
                            "R": {
                                "name": "Barry Moore"
                                "votes": 53055
                                "votes_pct": 75.5
                            }
                        },
                        "timestamp": "2024-11-13T07:55:26.402536"
                    },
                    "2": {
                        "pct_reported": 92.0
                        "total_votes": 102172
                        "candidates": {
                            // candidate party
                            "D": {
                                "name": "Shomari Figures",
                                "votes": 55309,
                                "votes_pct": 54.1,
                            },
                            "R": {
                                "name": "Caroleene Dobson",
                                "votes": 46782,
                                "votes_pct": 45.8,
                            }
                        },
                        "timestamp": "2024-11-13T07:55:26.402536"
                    }
                }
            }
        }
    }
}
    """
    data: Dict[int, Dict[str, Dict[str, Dict[str, List[int]]]]] = field(default_factory=dict)



@dataclass
class ElectionDataGroupedRowModel(RowModel):
    """
    Row model for grouped analysis. Aggregated from ElectionDataFullModel.
    """
    election_year: int
    election_type: str
    state_code: str
    county: str
    dem_candidate: Optional[str] = None
    rep_candidate: Optional[str] = None
    other_candidate: Optional[str] = None
    reported_pct: Optional[float] = None
    votes_total: Optional[int] = None
    votes_dem: Optional[int] = None
    votes_rep: Optional[int] = None
    votes_other: Optional[int] = None
    votes_dem_pct: Optional[float] = None
    votes_rep_pct: Optional[float] = None
    votes_other_pct: Optional[float] = None


@dataclass
class ElectionDataGroupedModel(CsvFileData[ElectionDataGroupedRowModel]):
    data: List[ElectionDataGroupedRowModel]

    @property
    def row_model(self) -> Type[ElectionDataGroupedRowModel]:
        return ElectionDataGroupedRowModel




@dataclass
class ElectionDataGroupedAndFlattenedRowModel(RowModel):
    """Row model for flattened election data with columns for each metric/year combination"""
    state_code: str
    county: str
    
    # 2024 Presidential
    pres_total_votes_2024: Optional[int] = None
    pres_total_votes_dem_2024: Optional[int] = None
    pres_total_votes_rep_2024: Optional[int] = None
    pres_total_votes_other_2024: Optional[int] = None
    pres_total_votes_dem_pct_2024: Optional[float] = None
    pres_total_votes_rep_pct_2024: Optional[float] = None
    pres_total_votes_other_pct_2024: Optional[float] = None
    pres_pct_reported_2024: Optional[float] = None
    
    # 2024 Senate
    senate_total_votes_2024: Optional[int] = None
    senate_total_votes_dem_2024: Optional[int] = None
    senate_total_votes_rep_2024: Optional[int] = None
    senate_total_votes_other_2024: Optional[int] = None
    senate_total_votes_dem_pct_2024: Optional[float] = None
    senate_total_votes_rep_pct_2024: Optional[float] = None
    senate_total_votes_other_pct_2024: Optional[float] = None
    senate_pct_reported_2024: Optional[float] = None
    
    # 2024 House
    house_total_votes_2024: Optional[int] = None
    house_total_votes_dem_2024: Optional[int] = None
    house_total_votes_rep_2024: Optional[int] = None
    house_total_votes_other_2024: Optional[int] = None
    house_total_votes_dem_pct_2024: Optional[float] = None
    house_total_votes_rep_pct_2024: Optional[float] = None
    house_total_votes_other_pct_2024: Optional[float] = None
    house_pct_reported_2024: Optional[float] = None
    
    # 2024 Governor
    gov_total_votes_2024: Optional[int] = None
    gov_total_votes_dem_2024: Optional[int] = None
    gov_total_votes_rep_2024: Optional[int] = None
    gov_total_votes_other_2024: Optional[int] = None
    gov_total_votes_dem_pct_2024: Optional[float] = None
    gov_total_votes_rep_pct_2024: Optional[float] = None
    gov_total_votes_other_pct_2024: Optional[float] = None
    gov_pct_reported_2024: Optional[float] = None
    
    # 2020 Presidential
    pres_total_votes_2020: Optional[int] = None
    pres_total_votes_dem_2020: Optional[int] = None
    pres_total_votes_rep_2020: Optional[int] = None
    pres_total_votes_other_2020: Optional[int] = None
    pres_total_votes_dem_pct_2020: Optional[float] = None
    pres_total_votes_rep_pct_2020: Optional[float] = None
    pres_total_votes_other_pct_2020: Optional[float] = None
    pres_pct_reported_2020: Optional[float] = None
    
    # 2020 Senate
    senate_total_votes_2020: Optional[int] = None
    senate_total_votes_dem_2020: Optional[int] = None
    senate_total_votes_rep_2020: Optional[int] = None
    senate_total_votes_other_2020: Optional[int] = None
    senate_total_votes_dem_pct_2020: Optional[float] = None
    senate_total_votes_rep_pct_2020: Optional[float] = None
    senate_total_votes_other_pct_2020: Optional[float] = None
    senate_pct_reported_2020: Optional[float] = None
    
    # 2020 House
    house_total_votes_2020: Optional[int] = None
    house_total_votes_dem_2020: Optional[int] = None
    house_total_votes_rep_2020: Optional[int] = None
    house_total_votes_other_2020: Optional[int] = None
    house_total_votes_dem_pct_2020: Optional[float] = None
    house_total_votes_rep_pct_2020: Optional[float] = None
    house_total_votes_other_pct_2020: Optional[float] = None
    house_pct_reported_2020: Optional[float] = None
    
    # 2020 Governor
    gov_total_votes_2020: Optional[int] = None
    gov_total_votes_dem_2020: Optional[int] = None
    gov_total_votes_rep_2020: Optional[int] = None
    gov_total_votes_other_2020: Optional[int] = None
    gov_total_votes_dem_pct_2020: Optional[float] = None
    gov_total_votes_rep_pct_2020: Optional[float] = None
    gov_total_votes_other_pct_2020: Optional[float] = None
    gov_pct_reported_2020: Optional[float] = None




@dataclass
class ElectionDataGroupedAndFlattenedModel(CsvFileData[ElectionDataGroupedAndFlattenedRowModel]):
    """Model for flattened election data that can be saved/loaded from CSV"""
    data: List[ElectionDataGroupedAndFlattenedRowModel]

    @property
    def row_model(self) -> Type[ElectionDataGroupedAndFlattenedRowModel]:
        return ElectionDataGroupedAndFlattenedRowModel