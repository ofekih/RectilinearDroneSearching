#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse

def visualize_square_data(data_file=None, output_dir=None):
    """
    Generate visualization plots for the aggregated square data.

    Args:
        data_file: Path to the aggregated data CSV file (default: 'data/aggregated_square_data.csv')
        output_dir: Directory to save output plots (default: same directory as data_file)
    """
    # Set default data file path
    if data_file is None:
        data_file = Path('data') / 'aggregated_square_data.csv'
    else:
        data_file = Path(data_file)

    # Set default output directory
    if output_dir is None:
        output_dir = data_file.parent
    else:
        output_dir = Path(output_dir)

    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)

    # Check if data file exists
    if not data_file.exists():
        print(f"Error: Data file {data_file} not found.")
        print("Run aggregate_square_data.py first to generate the aggregated data.")
        return

    # Load the aggregated data
    try:
        stats = pd.read_csv(data_file)
        print(f"Loaded aggregated data from {data_file}")

        # Add scaled metrics as requested:
        # - Scale down P by d * log2(n), where d is the dimension
        # - Scale down num_responses by d * log2(n)
        # - Scale down D by d * n
        stats['P_mean_scaled'] = stats['P_mean'] / (stats['dims'] * np.log2(stats['n']))
        stats['P_min_scaled'] = stats['P_min'] / (stats['dims'] * np.log2(stats['n']))
        stats['P_max_scaled'] = stats['P_max'] / (stats['dims'] * np.log2(stats['n']))
        stats['P_std_scaled'] = stats['P_std'] / (stats['dims'] * np.log2(stats['n']))

        stats['num_responses_mean_scaled'] = stats['num_responses_mean'] / (stats['dims'] * np.log2(stats['n']))
        stats['num_responses_min_scaled'] = stats['num_responses_min'] / (stats['dims'] * np.log2(stats['n']))
        stats['num_responses_max_scaled'] = stats['num_responses_max'] / (stats['dims'] * np.log2(stats['n']))
        stats['num_responses_std_scaled'] = stats['num_responses_std'] / (stats['dims'] * np.log2(stats['n']))

        stats['D_mean_scaled'] = stats['D_mean'] / (stats['dims'] * stats['n'])
        stats['D_min_scaled'] = stats['D_min'] / (stats['dims'] * stats['n'])
        stats['D_max_scaled'] = stats['D_max'] / (stats['dims'] * stats['n'])
        stats['D_std_scaled'] = stats['D_std'] / (stats['dims'] * stats['n'])

        print("Added scaled metrics:")
        print("- P scaled by d * log2(n), where d is the dimension")
        print("- num_responses scaled by d * log2(n)")
        print("- D scaled by d * n")
    except Exception as e:
        print(f"Error loading data file: {e}")
        return

    # Create a plots directory
    plots_dir = output_dir / 'plots'
    plots_dir.mkdir(exist_ok=True)

    # Set plot style
    sns.set(style="whitegrid")
    plt.rcParams.update({'font.size': 12})

    print("Generating visualization plots...")

    # 1. Plot P (number of probes) scaled by d * log2(n)
    plt.figure(figsize=(14, 10))
    # Create a new column combining algorithm and hiker_algorithm for better visualization
    stats['algorithm_hiker'] = stats['algorithm'] + ' (' + stats['hiker_algorithm'] + ')'
    # Sort stats by dims before plotting
    stats_sorted = stats.sort_values('dims')
    sns.barplot(x='dims', y='P_mean_scaled', hue='algorithm_hiker', data=stats_sorted)
    plt.title('Average Number of Probes by Dimension, Algorithm and Hiker Type (Scaled by d * log₂(n))')
    plt.xlabel('Dimension')
    plt.ylabel('Average Number of Probes (P / (d * log₂(n)))')
    plt.xticks(range(len(stats_sorted['dims'].unique())), sorted(stats_sorted['dims'].unique()))
    plt.legend(title='Algorithm (Hiker Type)', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(plots_dir / 'probes_by_dimension.png')
    plt.close()

    # 2. Plot D (distance traveled) scaled by d * n
    plt.figure(figsize=(14, 10))
    sns.barplot(x='dims', y='D_mean_scaled', hue='algorithm_hiker', data=stats_sorted)
    plt.title('Average Distance Traveled by Dimension, Algorithm and Hiker Type (Scaled by d * n)')
    plt.xlabel('Dimension')
    plt.ylabel('Average Distance Traveled (D / (d * n))')
    plt.xticks(range(len(stats_sorted['dims'].unique())), sorted(stats_sorted['dims'].unique()))
    plt.legend(title='Algorithm (Hiker Type)', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(plots_dir / 'distance_by_dimension.png')
    plt.close()

    # 3. Plot num_responses scaled by d * log2(n)
    plt.figure(figsize=(14, 10))
    sns.barplot(x='dims', y='num_responses_mean_scaled', hue='algorithm_hiker', data=stats_sorted)
    plt.title('Average Number of Responses by Dimension, Algorithm and Hiker Type (Scaled by d * log₂(n))')
    plt.xlabel('Dimension')
    plt.ylabel('Average Number of Responses (/ (d * log₂(n)))')
    plt.xticks(range(len(stats_sorted['dims'].unique())), sorted(stats_sorted['dims'].unique()))
    plt.legend(title='Algorithm (Hiker Type)', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(plots_dir / 'responses_by_dimension.png')
    plt.close()

    # 4. Plot D/hiker_distance vs dimension for each algorithm
    plt.figure(figsize=(14, 10))
    sns.barplot(x='dims', y='D_hiker_ratio_mean', hue='algorithm_hiker', data=stats_sorted)
    plt.title('Average D/Hiker Distance Ratio by Dimension, Algorithm and Hiker Type')
    plt.xlabel('Dimension')
    plt.ylabel('Average D/Hiker Distance Ratio')
    plt.xticks(range(len(stats_sorted['dims'].unique())), sorted(stats_sorted['dims'].unique()))
    plt.legend(title='Algorithm (Hiker Type)', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(plots_dir / 'distance_ratio_by_dimension.png')
    plt.close()

    # 5. Create line plots showing the growth of scaled metrics with dimension
    plt.figure(figsize=(14, 10))

    # Create subplots for each scaled metric
    scaled_metrics = ['P_mean_scaled', 'D_mean_scaled', 'num_responses_mean_scaled', 'D_hiker_ratio_mean']
    scaled_titles = ['Average Probes (P / (d * log₂(n)))', 'Average Distance (D / (d * n))',
                    'Average Responses (/ (d * log₂(n)))', 'Average D/Hiker Distance Ratio']

    for i, (metric, title) in enumerate(zip(scaled_metrics, scaled_titles)):
        plt.subplot(2, 2, i+1)

        # Plot the metric vs dimension for each algorithm and hiker type
        for algorithm_hiker in stats_sorted['algorithm_hiker'].unique():
            alg_data = stats_sorted[stats_sorted['algorithm_hiker'] == algorithm_hiker]
            alg_data = alg_data.sort_values('dims')
            plt.plot(alg_data['dims'], alg_data[metric], marker='o', label=algorithm_hiker)

        plt.title(title)
        plt.xlabel('Dimension')
        plt.ylabel(title)
        plt.grid(True)
        plt.legend()

    plt.tight_layout()
    plt.savefig(plots_dir / 'metrics_by_dimension.png')
    plt.close()

    # 6. Create a heatmap comparing algorithms across dimensions using scaled metrics
    # For each scaled metric, create a pivot table with dimensions as rows and algorithm_hiker as columns
    for metric, title in zip(scaled_metrics, scaled_titles):
        pivot = stats_sorted.pivot_table(index='dims', columns='algorithm_hiker', values=metric)
        pivot = pivot.sort_index()

        plt.figure(figsize=(14, 10))
        sns.heatmap(pivot, annot=True, cmap='viridis', fmt='.2f')
        plt.title(f'{title} by Dimension, Algorithm and Hiker Type')
        plt.tight_layout()
        plt.savefig(plots_dir / f'{metric}_heatmap.png')
        plt.close()

    # 8. Create a bar chart showing the efficiency of algorithms using scaled metrics
    # Efficiency defined as (P_mean_scaled * D_mean_scaled) - lower is better
    stats_sorted['efficiency_scaled'] = stats_sorted['P_mean_scaled'] * stats_sorted['D_mean_scaled']

    plt.figure(figsize=(14, 10))
    sns.barplot(x='dims', y='efficiency_scaled', hue='algorithm_hiker', data=stats_sorted)
    plt.title('Algorithm Efficiency by Dimension, Algorithm and Hiker Type (P/(d*log₂(n)) × D/(d*n), lower is better)')
    plt.xlabel('Dimension')
    plt.ylabel('Efficiency (P/(d*log₂(n)) × D/(d*n))')
    plt.xticks(range(len(stats_sorted['dims'].unique())), sorted(stats_sorted['dims'].unique()))
    plt.legend(title='Algorithm (Hiker Type)', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(plots_dir / 'algorithm_efficiency.png')
    plt.close()

    # 9. Create a normalized comparison chart using scaled metrics
    # Normalize metrics within each dimension to compare algorithms on equal footing
    normalized_stats = []

    for dim in sorted(stats_sorted['dims'].unique()):
        dim_stats = stats_sorted[stats_sorted['dims'] == dim].copy()

        # Normalize each metric (lower values are better)
        for metric in ['P_mean_scaled', 'D_mean_scaled', 'D_hiker_ratio_mean']:
            max_val = dim_stats[metric].max()
            if max_val > 0:
                dim_stats[f'{metric}_normalized'] = dim_stats[metric] / max_val

        # For num_responses, higher is better, so invert the normalization
        max_responses = dim_stats['num_responses_mean_scaled'].max()
        if max_responses > 0:
            dim_stats['num_responses_mean_scaled_normalized'] = dim_stats['num_responses_mean_scaled'] / max_responses

        normalized_stats.append(dim_stats)

    normalized_df = pd.concat(normalized_stats)

    # Create a radar chart-like visualization using a grouped bar chart
    plt.figure(figsize=(15, 10))

    for i, dim in enumerate(sorted(stats_sorted['dims'].unique())):
        plt.subplot(len(stats_sorted['dims'].unique()), 1, i+1)

        dim_data = normalized_df[normalized_df['dims'] == dim]
        metrics = ['P_mean_scaled_normalized', 'D_mean_scaled_normalized',
                  'num_responses_mean_scaled_normalized', 'D_hiker_ratio_mean_normalized']

        # Reshape data for grouped bar chart
        plot_data = []
        for _, row in dim_data.iterrows():
            for metric in metrics:
                if metric in row:
                    plot_data.append({
                        'algorithm': row['algorithm_hiker'],
                        'metric': metric.replace('_normalized', '').replace('_scaled', ' (scaled)'),
                        'value': row[metric]
                    })

        plot_df = pd.DataFrame(plot_data)
        # Sort plot_df by metric for consistent x-axis
        plot_df = plot_df.sort_values('metric')
        sns.barplot(x='metric', y='value', hue='algorithm', data=plot_df)

        plt.title(f'Normalized Scaled Metrics Comparison in {dim}D by Algorithm and Hiker Type')
        plt.xlabel('')
        plt.ylabel('Normalized Value (0-1)')
        plt.ylim(0, 1.1)

        # Only show legend on the last subplot
        if i == len(stats_sorted['dims'].unique()) - 1:
            plt.legend(title='Algorithm')
        else:
            plt.legend([],[], frameon=False)

    plt.tight_layout()
    plt.savefig(plots_dir / 'normalized_comparison.png')
    plt.close()

    print(f"Visualization plots saved to {plots_dir}")

def main():
    """Main function to run the visualization."""
    parser = argparse.ArgumentParser(description='Visualize aggregated square data.')
    parser.add_argument('--data-file', type=str, default=None,
                        help='Path to the aggregated data CSV file (default: data/aggregated_square_data.csv)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Directory to save output plots (default: same directory as data file)')

    args = parser.parse_args()

    visualize_square_data(data_file=args.data_file, output_dir=args.output_dir)

if __name__ == "__main__":
    main()
