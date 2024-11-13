import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Tuple

def plot_comparison_bar_chart(
    non_swing_2020: float,
    non_swing_2024: float,
    swing_2020: float,
    swing_2024: float,
    title: str,
    subtitle: Optional[str] = None,
    y_label: Optional[str] = None,
    y_bounds: Optional[Tuple[float, float]] = None,
    figsize: tuple = (10, 6)
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
    plt.show()