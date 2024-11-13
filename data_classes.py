import csv
import abc
import json
import os
import time
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, asdict, fields, is_dataclass, field
from typing import List, Type, TypeVar, Union, Dict, Any, Optional, Generic, ClassVar

T = TypeVar('T', bound='RowModel')

@dataclass
class JsonFileData:
    data: Dict
    
    def save_to_json(self, filename: Union[str, list[str]]):
        """Saves the data to a JSON file."""
        filepath = filename if isinstance(filename, str) else os.path.join(*filename)
        with open(filepath, 'w') as f:
            json.dump(self.data, f, indent=4)
        print(f"Data saved to {filepath}")

    @classmethod
    def load_from_json(cls, filename: Union[str, list[str]]) -> 'JsonFileData':
        """Loads data from a JSON file and returns an instance of JsonFileData."""
        filepath = filename if isinstance(filename, str) else os.path.join(*filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(data)
        
class RowModel:
    """Base class for CSV row models with serialization/deserialization methods."""

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary."""
        if is_dataclass(self):
            return asdict(self)
        raise TypeError("RowModel must be a dataclass")

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Creates an instance of the dataclass from a dictionary, handling type conversions."""
        field_types = {field.name: field.type for field in fields(cls)}
        kwargs = {}

        for key, value in data.items():
            # Convert the value to the appropriate type if it is not None
            target_type = field_types.get(key)
            if value is not None and target_type:
                # Handle Optional types
                if hasattr(target_type, '__origin__') and target_type.__origin__ is Union:
                    # Get the actual type from the Optional
                    actual_type = next(t for t in target_type.__args__ if t is not type(None))
                    try:
                        # Convert string 'None' to None
                        if value == 'None' or value == '':
                            kwargs[key] = None
                        else:
                            kwargs[key] = actual_type(value)
                    except (ValueError, TypeError):
                        kwargs[key] = None
                else:
                    try:
                        kwargs[key] = target_type(value)
                    except (ValueError, TypeError):
                        kwargs[key] = None
            else:
                kwargs[key] = value

        return cls(**kwargs)


class CsvFileData(Generic[T], abc.ABC):
    data: List[T]

    @property
    @abc.abstractmethod
    def row_model(self) -> Type[T]:
        """Returns the row model class associated with this CSV file."""
        pass

    def save_to_csv(self, filename: Union[str, List[str]]):
        """Saves the data to a CSV file."""
        filepath = filename if isinstance(filename, str) else os.path.join(*filename)
        
        # Use the field names from the row model for CSV headers
        fieldnames = [field.name for field in fields(self.row_model)]
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.data:
                writer.writerow(row.to_dict())
        
        print(f"Data saved to {filepath}")

    @classmethod
    def load_from_csv(cls: Type['CsvFileData[T]'], filename: Union[str, List[str]]) -> 'CsvFileData[T]':
        """Loads data from a CSV file and returns an instance of CsvFileData."""
        filepath = filename if isinstance(filename, str) else os.path.join(*filename)
        data = []

        # Create an instance of the class to access the row_model property
        instance = cls(data=[])  # Create temporary instance with empty data
        row_model_class = instance.row_model  # Get the actual row model class

        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Use the row_model's from_dict method to create instances
                data_row = row_model_class.from_dict(row)
                data.append(data_row)
        
        return cls(data=data)
    
    
    def to_dataframe(self) -> pd.DataFrame:
        """Converts the data to a pandas DataFrame."""
        # Convert each row to a dictionary and create DataFrame
        return pd.DataFrame([row.to_dict() for row in self.data])