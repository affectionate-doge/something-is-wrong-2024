import requests
import csv
import abc
import pandas as pd
import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, asdict, fields, is_dataclass
from typing import List, Type, TypeVar, Union, Dict, Any, Optional, Generic
from datetime import datetime

from data_model import *



class DataFunctions:

    @staticmethod
    def get_election_year_state_district_county_map(years: list[int], states: list[str]) -> ElectionYearStateCountyDistrictMap:
        res = {}
        for year in years:
            print(f'Loading year {year}...')
            res[year] = {}
            for state in states:
                counties = []
                districts = []
                county_districts = {}
                
                # Pull counties for pres race
                url = f"https://politics.api.cnn.io/results/county-races/{year}-PG-{state}.json"
                response = requests.get(url)
                if response.status_code == 200:
                    for county_data in response.json():
                        county_name = county_data["countyName"]
                        if county_name not in counties:
                            counties.append(county_name)
                        else:
                            raise Exception(f"Duplicate county name '{county_name}' for presidential election results in state '{state}', year {year}. Url: {url}")
                else:
                    raise Exception(f"Failed request for presidential election results in state '{state}', year {year}. Url: {url}")

                # Pull districts for house races
                district_id = 1
                while True:
                    url = f"https://politics.api.cnn.io/results/county-races/{year}-HG-{state}-{district_id}.json"
                    response = requests.get(url)
                    if response.status_code == 200:
                        districts.append(district_id)
                        for county_data in response.json():
                            county_name = county_data["countyName"]
                            if county_name not in counties:
                                raise Exception(f"County '{county_name}' from house results not present in presidential results in state '{state}', year {year}. Url: {url}")
                            if county_name not in county_districts:
                                county_districts[county_name] = [district_id]
                            else:
                                county_districts[county_name].append(district_id)
                        district_id += 1
                    else:
                        time.sleep(1)
                        # Retry on error... if errors again, assume there are no more districts
                        response = requests.get(url)
                        if response.status_code == 200:
                            districts.append(district_id)
                            for county_data in response.json():
                                county_name = county_data["countyName"]
                                if county_name not in counties:
                                    raise Exception(f"County '{county_name}' from house results not present in presidential results in state '{state}', year {year}. Url: {url}")
                                if county_name not in county_districts:
                                    county_districts[county_name] = [district_id]
                                else:
                                    county_districts[county_name].append(district_id)
                            district_id += 1
                        else:
                            break

                for c in counties:
                    if not c in county_districts.keys():
                        county_districts[c] = []

                print(f'    Loaded {state}... {len(counties)} counties, {len(districts)} districts')
                res[year][state] = {"counties": counties, "districts": districts, "county_districts": county_districts}

        return ElectionYearStateCountyDistrictMap(res)


    @staticmethod
    def get_all_election_data(election_types: list[str], year_state_county_district_map: ElectionYearStateCountyDistrictMap) -> ElectionDataFullModel:

        def get_blank_county_data() -> dict[str, any]:
            return { 
                "pct_reported": None,
                "total_votes": None,
                "candidates": {},
                "timestamp": None
            }

        def extract_county_data_from_response(county_response_data: json) -> dict[str, any]:
            data = { 
                "pct_reported": county_response_data["percentReporting"],
                "total_votes": county_response_data["totalVote"],
                "candidates": {
                    candidate["candidatePartyCode"]: {
                        "name": candidate["fullName"],
                        "votes": candidate["voteNum"],
                        "votes_pct": float(candidate["votePercentStr"])
                    }
                    for candidate in county_response_data["candidates"]
                },
                "timestamp": county_response_data["extractedAt"]
            }
            return data

        res = {}
        for year, states in year_state_county_district_map.data.items():
            print('Loading year...')
            year_data = {}
            for state in states:
                state_counties = year_state_county_district_map.data[year][state]["counties"]
                state_counties_data = {}
                
                # Populate empty values for each county and election type (include district in key for house elections)
                for county_name in state_counties:
                    state_counties_data[county_name] = {}
                    for election_type in election_types:
                        if election_type != 'H':
                            state_counties_data[county_name][election_type] = get_blank_county_data()
                        else:
                            state_counties_data[county_name][election_type] = {}
                            try:
                                for district in year_state_county_district_map.data[year][state]["county_districts"][county_name]:
                                    state_counties_data[county_name][election_type][district] = get_blank_county_data()
                            except Exception as ex:
                                print(f'Err generating data. Year: {year}, State: {state}, election type: {election_type}, county: {county_name}')



                for election_type in election_types:                    
                    loaded_counties = set()
                    if election_type in ('P', 'S', 'G'):
                        # load county data
                        url = f"https://politics.api.cnn.io/results/county-races/{year}-{election_type}G-{state}.json"
                        response = requests.get(url)
                        if response.status_code == 200:
                            for county_response_data in response.json():
                                county_name = county_response_data["countyName"]
                                state_counties_data[county_name][election_type] = extract_county_data_from_response(county_response_data)
                                if not county_name in loaded_counties:
                                    loaded_counties.add(county_name)  
                                else:
                                    raise Exception(f"Duplicate county {county_name} for state {state}, year {year}, election type: {election_type}.")                     
                        else:
                            time.sleep(1)
                            if response.status_code == 200:
                                for county_response_data in response.json():
                                    county_name = county_response_data["countyName"]
                                    state_counties_data[county_name][election_type] = extract_county_data_from_response(county_response_data)   
                                    if not county_name in loaded_counties:
                                        loaded_counties.add(county_name)      
                                    else:
                                        raise Exception(f"Duplicate county {county_name} for state {state}, year {year}, election type: {election_type}.")                                                                               

                    elif election_type == 'H':
                        # load district county data
                        for district in year_state_county_district_map.data[year][state]["districts"]:
                            url = f"https://politics.api.cnn.io/results/county-races/{year}-{election_type}G-{state}-{district}.json"
                            response = requests.get(url)
                            if response.status_code == 200:
                                for county_response_data in response.json():
                                    county_name = county_response_data["countyName"]
                                    state_counties_data[county_name][election_type][district] = extract_county_data_from_response(county_response_data)
                                    if not county_name in loaded_counties:
                                        loaded_counties.add(county_name)
                            else:
                                time.sleep(1)
                                if response.status_code == 200:
                                    for county_response_data in response.json():
                                        county_name = county_response_data["countyName"]
                                        state_counties_data[county_name][election_type][district] = extract_county_data_from_response(county_response_data)   
                                        if not county_name in loaded_counties:
                                            loaded_counties.add(county_name)
                    else:
                        raise Exception(f"Unsupported election_type '{election_type}'")
                    
                    # Confirm all counties present if any are present (if none are present means race didn't happen)
                    # if len(loaded_counties) > 0:
                    #     if len(loaded_counties) != len(state_counties):
                    #         diff = set(state_counties).difference(set([c for c in state_counties_data[election_type].keys()]))
                    #         raise Exception(f"Inconsistent counties for state {state}, year {year}, election type: {election_type}. Difference: {diff}")
                    
                
                # Load state data to year data
                year_data[state] = state_counties_data
                print(f' Loaded state {state}')
                # for election_type in election_types:
                #     print(f"        '{election_type}': {len(state_counties_data[election_type])} records")

            
            # Load year data to results
            res[year] = year_data
        
        return ElectionDataFullModel(res)

    @staticmethod        
    def aggregate_full_data_to_grouped(full_data: ElectionDataFullModel) -> ElectionDataGroupedModel:
        # Dictionary to store aggregated data, keyed by (year, state, election_type, county)
        aggregated_data = {}
        
        for year, state_data in full_data.data.items():
            for state_code, county_data in state_data.items():
                for county, election_types in county_data.items():
                    for election_type, data in election_types.items():
                        key = (year, state_code, election_type, county)
                        
                        if election_type == 'H':
                            # Initialize aggregated data for this key if not exists
                            if key not in aggregated_data:
                                aggregated_data[key] = {
                                    'dem_candidates': [],
                                    'rep_candidates': [],
                                    'other_candidates': [],
                                    'dem_votes': 0,
                                    'rep_votes': 0,
                                    'other_votes': 0,
                                    'total_votes': 0,
                                    'district_weights': []  # Store district total votes and reported percentages for weighted average
                                }
                            
                            # Iterate through each district's data
                            for district, district_data in data.items():
                                if not district_data['candidates']:
                                    continue
                                
                                # Store district's total votes and reported percentage for weighted average
                                district_total_votes = district_data.get('total_votes', 0)
                                if district_total_votes > 0 and district_data['pct_reported'] is not None:
                                    aggregated_data[key]['district_weights'].append({
                                        'total_votes': district_total_votes,
                                        'pct_reported': district_data['pct_reported']
                                    })
                                
                                # Process each candidate
                                for party, candidate_data in district_data['candidates'].items():
                                    candidate_name = f"[{district}]{candidate_data['name']}"
                                    votes = candidate_data['votes']
                                    
                                    if party == 'D':
                                        aggregated_data[key]['dem_candidates'].append(candidate_name)
                                        aggregated_data[key]['dem_votes'] += votes
                                    elif party == 'R':
                                        aggregated_data[key]['rep_candidates'].append(candidate_name)
                                        aggregated_data[key]['rep_votes'] += votes
                                    else:
                                        aggregated_data[key]['other_candidates'].append(candidate_name)
                                        aggregated_data[key]['other_votes'] += votes
                                    
                                    aggregated_data[key]['total_votes'] += votes
                            
                        else:  # Non-House elections (P, S, G)
                            if not data['candidates']:
                                continue
                                
                            aggregated_data[key] = {
                                'dem_candidates': [],
                                'rep_candidates': [],
                                'other_candidates': [],
                                'dem_votes': 0,
                                'rep_votes': 0,
                                'other_votes': 0,
                                'total_votes': 0,
                                'reported_pct': data['pct_reported']
                            }
                            
                            # Process each candidate
                            for party, candidate_data in data['candidates'].items():
                                votes = candidate_data['votes']
                                
                                if party == 'D':
                                    aggregated_data[key]['dem_candidates'].append(candidate_data['name'])
                                    aggregated_data[key]['dem_votes'] += votes
                                elif party == 'R':
                                    aggregated_data[key]['rep_candidates'].append(candidate_data['name'])
                                    aggregated_data[key]['rep_votes'] += votes
                                else:
                                    aggregated_data[key]['other_candidates'].append(candidate_data['name'])
                                    aggregated_data[key]['other_votes'] += votes
                                
                                aggregated_data[key]['total_votes'] += votes
        
        # Convert aggregated data to rows
        grouped_rows = []
        for (year, state_code, election_type, county), data in aggregated_data.items():
            # For House races, calculate weighted average of reported percentage
            if election_type == 'H' and data.get('district_weights', []):
                weights = data['district_weights']
                total_weight = sum(d['total_votes'] for d in weights)
                if total_weight > 0:
                    weighted_pct = sum(
                        d['pct_reported'] * (d['total_votes'] / total_weight) 
                        for d in weights
                    )
                    reported_pct = weighted_pct
                else:
                    reported_pct = None
            else:
                reported_pct = data.get('reported_pct')
                
            # Calculate vote percentages
            total_votes = data['total_votes']
            dem_pct = (data['dem_votes'] / total_votes * 100) if total_votes > 0 else None
            rep_pct = (data['rep_votes'] / total_votes * 100) if total_votes > 0 else None
            other_pct = (data['other_votes'] / total_votes * 100) if total_votes > 0 else None
            
            # Create row
            grouped_row = ElectionDataGroupedRowModel(
                election_year=year,
                election_type=election_type,
                state_code=state_code,
                county=county,
                dem_candidate='; '.join(data['dem_candidates']) if data['dem_candidates'] else None,
                rep_candidate='; '.join(data['rep_candidates']) if data['rep_candidates'] else None,
                other_candidate='; '.join(data['other_candidates']) if data['other_candidates'] else None,
                reported_pct=reported_pct,
                votes_total=total_votes,
                votes_dem=data['dem_votes'],
                votes_rep=data['rep_votes'],
                votes_other=data['other_votes'],
                votes_dem_pct=dem_pct,
                votes_rep_pct=rep_pct,
                votes_other_pct=other_pct
            )
            grouped_rows.append(grouped_row)
        
        return ElectionDataGroupedModel(data=grouped_rows)


        
    @staticmethod        
    def flatten_grouped_election_data(grouped_data: ElectionDataGroupedModel) -> ElectionDataGroupedAndFlattenedModel:
        """
        Converts grouped election data into flattened format with one row per state/county
        """
        # Dictionary to store flattened data, keyed by (state_code, county)
        flattened_data = {}
        
        # Process each row in grouped data
        for row in grouped_data.data:
            key = (row.state_code, row.county)
            
            # Initialize new row if needed
            if key not in flattened_data:
                flattened_data[key] = ElectionDataGroupedAndFlattenedRowModel(
                    state_code=row.state_code,
                    county=row.county
                )
            
            # Map to flatten format field names
            field_prefix = {
                'P': 'pres',
                'S': 'senate',
                'H': 'house',
                'G': 'gov'
            }[row.election_type]
            
            # Get the target row
            flat_row = flattened_data[key]
            
            # Set fields based on year and election type
            year = str(row.election_year)
            
            # Total votes
            setattr(flat_row, f"{field_prefix}_total_votes_{year}", row.votes_total)
            
            # Democratic votes
            setattr(flat_row, f"{field_prefix}_total_votes_dem_{year}", row.votes_dem)
            setattr(flat_row, f"{field_prefix}_total_votes_dem_pct_{year}", row.votes_dem_pct)
            
            # Republican votes
            setattr(flat_row, f"{field_prefix}_total_votes_rep_{year}", row.votes_rep)
            setattr(flat_row, f"{field_prefix}_total_votes_rep_pct_{year}", row.votes_rep_pct)
            
            # Other votes
            setattr(flat_row, f"{field_prefix}_total_votes_other_{year}", row.votes_other)
            setattr(flat_row, f"{field_prefix}_total_votes_other_pct_{year}", row.votes_other_pct)
            
            # Reported percentage
            setattr(flat_row, f"{field_prefix}_pct_reported_{year}", row.reported_pct)
        
        # Convert dictionary to list of rows
        flattened_rows = list(flattened_data.values())
        
        return ElectionDataGroupedAndFlattenedModel(data=flattened_rows)