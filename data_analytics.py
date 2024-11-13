import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

from typing import List, Dict, Optional, Tuple, Union
from data_model import ElectionDataGroupedAndFlattenedModel

class DataAnalytics:
    SWING_STATES = [
        'AZ', 'GA', 'MI', 'NV', 'PA', 'WI', 'NC'
    ]

    def __init__(self, data: ElectionDataGroupedAndFlattenedModel):
        self.df = data.to_dataframe()
        self._calculate_all_metrics(self.df)
    
    @staticmethod
    def _reorder_comprehensive_analysis_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Helper method to reorder columns with category, state_code, and county first."""
        first_cols = ['category', 'state_code', 'county']
        other_cols = [col for col in df.columns if col not in first_cols]
        return df[first_cols + other_cols]

    def analyze_presidential_house_ratios_comprehensive(self) -> pd.DataFrame:
        """
        Creates a comprehensive analysis of presidential to house vote ratios,
        including nationwide, swing states, and per-state anomalies.
        Separates increases and decreases in ratios.
        """
        # Create a clean working copy with finite values only
        working_df = self.df.copy()
        working_df = working_df[
            np.isfinite(working_df['pres_house_ratio_2024']) & 
            np.isfinite(working_df['pres_house_ratio_2020']) &
            np.isfinite(working_df['pres_house_ratio_change'])
        ]
        
        # Helper function to format ratio metrics
        def format_ratio_metrics(df: pd.DataFrame) -> pd.Series:
            if len(df) == 0:
                return pd.Series({
                    'county_count': 0,
                    'avg_ratio_2024': np.nan,
                    'avg_ratio_2020': np.nan,
                    'avg_ratio_change': np.nan,
                    'max_ratio_change': np.nan,
                    'min_ratio_change': np.nan,
                    'std_ratio_change': np.nan
                })
            
            return pd.Series({
                'county_count': len(df),
                'avg_ratio_2024': df['pres_house_ratio_2024'].mean(),
                'avg_ratio_2020': df['pres_house_ratio_2020'].mean(),
                'avg_ratio_change': df['pres_house_ratio_change'].mean(),
                'max_ratio_change': df['pres_house_ratio_change'].max(),
                'min_ratio_change': df['pres_house_ratio_change'].min(),
                'std_ratio_change': df['pres_house_ratio_change'].std()
            })

        results = []
        
        # 1. Nationwide stats
        nationwide = format_ratio_metrics(working_df)
        nationwide['category'] = 'Nationwide'
        nationwide['state_code'] = 'ALL'
        results.append(nationwide)
        
        # 2. Swing States aggregate
        swing_df = working_df[working_df['state_code'].isin(self.SWING_STATES)]
        swing_stats = format_ratio_metrics(swing_df)
        swing_stats['category'] = 'Swing States Aggregate'
        swing_stats['state_code'] = 'SWING'
        results.append(swing_stats)
        
        # 3. Non-Swing States aggregate
        nonswing_df = working_df[~working_df['state_code'].isin(self.SWING_STATES)]
        nonswing_stats = format_ratio_metrics(nonswing_df)
        nonswing_stats['category'] = 'Non-Swing States Aggregate'
        nonswing_stats['state_code'] = 'NON-SWING'
        results.append(nonswing_stats)
        
        # 4. Largest increases per swing state
        for state in self.SWING_STATES:
            state_df = working_df[working_df['state_code'] == state]
            if len(state_df) > 0:
                top_3 = state_df.nlargest(3, 'pres_house_ratio_change')
                
                for _, row in top_3.iterrows():
                    results.append(pd.Series({
                        'category': f'Top 2 Increase - {state}',
                        'state_code': state,
                        'county_count': 1,
                        'county': row['county'],
                        'avg_ratio_2024': row['pres_house_ratio_2024'],
                        'avg_ratio_2020': row['pres_house_ratio_2020'],
                        'avg_ratio_change': row['pres_house_ratio_change']
                    }))
        
        # 5. Top 5 increases nationwide
        top_5_increases = working_df.nlargest(5, 'pres_house_ratio_change')
        for _, row in top_5_increases.iterrows():
            results.append(pd.Series({
                'category': 'Top 5 Increase - Nationwide',
                'state_code': row['state_code'],
                'county_count': 1,
                'county': row['county'],
                'avg_ratio_2024': row['pres_house_ratio_2024'],
                'avg_ratio_2020': row['pres_house_ratio_2020'],
                'avg_ratio_change': row['pres_house_ratio_change']
            }))
        
        # 6. Top 5 decreases nationwide
        top_5_decreases = working_df.nsmallest(5, 'pres_house_ratio_change')
        for _, row in top_5_decreases.iterrows():
            results.append(pd.Series({
                'category': 'Top 5 Decrease - Nationwide',
                'state_code': row['state_code'],
                'county_count': 1,
                'county': row['county'],
                'avg_ratio_2024': row['pres_house_ratio_2024'],
                'avg_ratio_2020': row['pres_house_ratio_2020'],
                'avg_ratio_change': row['pres_house_ratio_change']
            }))
        
        results_df = pd.DataFrame(results)
        return self._reorder_comprehensive_analysis_columns(results_df)

    def analyze_split_ticket_voting_comprehensive(self) -> pd.DataFrame:
        """
        Creates a comprehensive analysis of split-ticket voting patterns,
        including nationwide, swing states, and separated increases/decreases.
        """
        # Create a clean working copy excluding NaN values
        working_df = self.df.copy()
        working_df = working_df[
            np.isfinite(working_df['split_ticket_2024']) & 
            np.isfinite(working_df['split_ticket_2020']) &
            np.isfinite(working_df['split_ticket_change'])
        ]
        
        # Helper function to format split ticket metrics
        def format_split_ticket_metrics(df: pd.DataFrame) -> pd.Series:
            if len(df) == 0:
                return pd.Series({
                    'county_count': 0,
                    'avg_split_ticket_2024': np.nan,
                    'avg_split_ticket_2020': np.nan,
                    'avg_split_ticket_change': np.nan,
                    'max_split_ticket_change': np.nan,
                    'min_split_ticket_change': np.nan,
                    'std_split_ticket_change': np.nan
                })
                
            return pd.Series({
                'county_count': len(df),
                'avg_split_ticket_2024': df['split_ticket_2024'].mean(),
                'avg_split_ticket_2020': df['split_ticket_2020'].mean(),
                'avg_split_ticket_change': df['split_ticket_change'].mean(),
                'max_split_ticket_change': df['split_ticket_change'].max(),
                'min_split_ticket_change': df['split_ticket_change'].min(),
                'std_split_ticket_change': df['split_ticket_change'].std()
            })

        results = []
        
        # 1. Nationwide stats
        nationwide = format_split_ticket_metrics(working_df)
        nationwide['category'] = 'Nationwide'
        nationwide['state_code'] = 'ALL'
        results.append(nationwide)
        
        # 2. Swing States aggregate
        swing_df = working_df[working_df['state_code'].isin(self.SWING_STATES)]
        swing_stats = format_split_ticket_metrics(swing_df)
        swing_stats['category'] = 'Swing States Aggregate'
        swing_stats['state_code'] = 'SWING'
        results.append(swing_stats)
        
        # 3. Non-Swing States aggregate
        nonswing_df = working_df[~working_df['state_code'].isin(self.SWING_STATES)]
        nonswing_stats = format_split_ticket_metrics(nonswing_df)
        nonswing_stats['category'] = 'Non-Swing States Aggregate'
        nonswing_stats['state_code'] = 'NON-SWING'
        results.append(nonswing_stats)
        
        # 4. Largest increases per swing state
        for state in self.SWING_STATES:
            state_df = working_df[working_df['state_code'] == state]
            if len(state_df) > 0:
                top_3 = state_df.nlargest(3, 'split_ticket_change')
                
                for _, row in top_3.iterrows():
                    results.append(pd.Series({
                        'category': f'Top 2 Increase - {state}',
                        'state_code': state,
                        'county_count': 1,
                        'county': row['county'],
                        'avg_split_ticket_2024': row['split_ticket_2024'],
                        'avg_split_ticket_2020': row['split_ticket_2020'],
                        'avg_split_ticket_change': row['split_ticket_change']
                    }))
        
        # 5. Top 5 increases nationwide
        top_5_increases = working_df.nlargest(5, 'split_ticket_change')
        for _, row in top_5_increases.iterrows():
            results.append(pd.Series({
                'category': 'Top 5 Increase - Nationwide',
                'state_code': row['state_code'],
                'county_count': 1,
                'county': row['county'],
                'avg_split_ticket_2024': row['split_ticket_2024'],
                'avg_split_ticket_2020': row['split_ticket_2020'],
                'avg_split_ticket_change': row['split_ticket_change']
            }))
        
        # 6. Top 5 decreases nationwide
        top_5_decreases = working_df.nsmallest(5, 'split_ticket_change')
        for _, row in top_5_decreases.iterrows():
            results.append(pd.Series({
                'category': 'Top 5 Decrease - Nationwide',
                'state_code': row['state_code'],
                'county_count': 1,
                'county': row['county'],
                'avg_split_ticket_2024': row['split_ticket_2024'],
                'avg_split_ticket_2020': row['split_ticket_2020'],
                'avg_split_ticket_change': row['split_ticket_change']
            }))
        
        results_df = pd.DataFrame(results)
        return self._reorder_comprehensive_analysis_columns(results_df)

    @staticmethod
    def _calculate_all_metrics(df: pd.DataFrame) -> None:
        """Helper method to calculate all metrics used in analysis."""
        # Calculate ratios, handling division by zero
        df['pres_house_ratio_2024'] = df['pres_total_votes_2024'].div(df['house_total_votes_2024'])
        df['pres_house_ratio_2020'] = df['pres_total_votes_2020'].div(df['house_total_votes_2020'])
        df['pres_house_ratio_change'] = df['pres_house_ratio_2024'] - df['pres_house_ratio_2020']
        df['abs_ratio_change'] = df['pres_house_ratio_change'].abs()
        
        # Calculate split ticket estimates
        for year in ['2024', '2020']:
            # Get total presidential and house votes
            pres_total = df[f'pres_total_votes_{year}']
            house_total = df[f'house_total_votes_{year}']
            
            # Get straight ticket vote estimates (minimum votes for each party across races)
            dem_straight = np.minimum(
                df[f'pres_total_votes_dem_{year}'],
                df[f'house_total_votes_dem_{year}']
            )
            rep_straight = np.minimum(
                df[f'pres_total_votes_rep_{year}'],
                df[f'house_total_votes_rep_{year}']
            )
            
            # Calculate total potential two-race voters and straight ticket voters
            total_votes = np.minimum(pres_total, house_total)  # Conservative estimate of two-race voters
            straight_votes = dem_straight + rep_straight
            
            # Calculate split ticket percentage
            split_votes = total_votes - straight_votes
            df[f'split_ticket_{year}'] = (split_votes / total_votes) * 100
            
            # Store underlying metrics for reference
            df[f'total_two_race_voters_{year}'] = total_votes
            df[f'straight_ticket_voters_{year}'] = straight_votes
            df[f'split_ticket_voters_{year}'] = split_votes
        
        # Calculate split ticket changes
        df['split_ticket_change'] = df['split_ticket_2024'] - df['split_ticket_2020']
        df['abs_split_ticket_change'] = df['split_ticket_change'].abs()

        
    @staticmethod
    def plot_comparison_bar_chart(
        non_swing_2020: float,
        non_swing_2024: float,
        swing_2020: float,
        swing_2024: float,
        title: str,
        subtitle: Optional[str] = None,
        y_label: Optional[str] = None,
        y_bounds: Optional[Tuple[float, float]] = None,
        figsize: tuple = (10, 6),    
        save_path: Optional[Union[str, list[str]]] = None
    ) -> None:
        """
        Creates a simple comparison bar chart showing 2020 vs 2024 values for swing and non-swing states.
        """
        # Create figure
        plt.figure(figsize=figsize)
        ax = plt.gca()

        # Set up positions for bars
        x = np.arange(2)
        width = 0.35
        
        # Create bars using the values directly
        values_2020 = [non_swing_2020*100, swing_2020*100]
        values_2024 = [non_swing_2024*100, swing_2024*100]
        
        plt.bar(x - width/2, values_2020, width, label='2020', color='lightskyblue')
        plt.bar(x + width/2, values_2024, width, label='2024', color='tomato')
        
        # Add value labels on top of bars
        for i, v in enumerate(values_2020):
            plt.text(i - width/2, v, f'{v:.2f}%', ha='center', va='bottom')
        for i, v in enumerate(values_2024):
            plt.text(i + width/2, v, f'{v:.2f}%', ha='center', va='bottom')

        
        # Customize plot
        t = title if not subtitle else f'{title}\n{subtitle}'
        plt.title(t, pad=20)
        if y_label:
            plt.ylabel(y_label)
        plt.xticks(x, ['Non-Swing States', 'Swing States'])
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Format y-axis as percentage
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}%'))
        
        # Set y-axis bounds if provided
        if y_bounds:
            plt.ylim(y_bounds)
        else:
            # Add some padding above the highest bar for the change labels
            current_ymax = plt.ylim()[1]
            plt.ylim(plt.ylim()[0], current_ymax * 1.1)

        # Add change values in small white boxes just below x-axis labels
        for i, (v1, v2) in enumerate(zip(values_2020, values_2024)):
            change = v2 - v1
            box_text = f'Change: {change:+.2f}%'
            
            # Position box just below x-axis labels
            ax.text(i, -0.15, box_text,
                ha='center', va='top',
                transform=ax.get_xaxis_transform(),
                bbox=dict(facecolor='white', 
                            edgecolor='gray',
                            alpha=0.9,
                            pad=0.5,
                            boxstyle='round'),
                size=9)  # Smaller font size

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)

        if save_path is not None:
            image_file_path = save_path if isinstance(save_path, str) else os.path.join(*save_path)
            plt.savefig(image_file_path, dpi=300, bbox_inches='tight')
        
        plt.show()
        plt.close()