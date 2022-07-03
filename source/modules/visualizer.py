# %%
# Python modules. 
import numpy as np 
import pandas as pd 
import altair as alt 
import umap.plot 
from matplotlib import pyplot as plt 
from scipy.cluster.hierarchy import dendrogram 

# Custom configs. 
from source.config_py.config import PARAM_N_TOPIC 



# %%
def plot_similarity(data, x:str, y:str, z:str, zlim:list=[0,1], format_text:str=".2f"): 
    height, width = 500, 800
    chart_title = "Topic Similarity" 

	# Topic names. 
    topic_names = [f"TP{topic_i}" for topic_i in range(0, PARAM_N_TOPIC)] 

    # Base encoding. 
    base = alt.Chart(data) \
        .encode(
            x=alt.X(
                f"{x}:N", 
                axis=alt.Axis(title="", titleFontSize=14, labelFontSize=10, labelAngle=0), 
                sort=topic_names, 
            ),
            y=alt.Y(
                f"{y}:N", 
                axis=alt.Axis(title="", titleFontSize=14, labelFontSize=10), 
                sort=topic_names, 
            ), 
            tooltip=[
                alt.Tooltip(f"{x}:N", title=x), 
                alt.Tooltip(f"{y}:N", title=y), 
                alt.Tooltip(f"{z}:Q", title=z, format=format_text), 
            ], 
        ) \
        .properties(title=chart_title, height=height, width=width) 

    # Visualisation approach. 
    chart = base \
        .mark_rect(opacity=1) \
        .encode(
            color=alt.Color(
                f"{z}:Q", 
                scale=alt.Scale(domain=zlim, scheme="blues", reverse=False),
                legend=alt.Legend(title="", direction="vertical"), 
            )
        ) 

    # Annotation. 
    text = base \
        .mark_text(baseline="middle") \
        .encode(text=alt.Text(f"{z}:Q", format=format_text)) \
        .properties(title=chart_title, height=height, width=width) 

    return (chart + text).interactive() 



# %%
def plot_token_weight(data, x:str, y:str, column:int=4, xlim:tuple=(0,1), format_text:str=".2f"): 
    height, width = 250, 100 

    topics = data["topic"].unique() 
    charts, row = alt.vconcat(), alt.hconcat() 

    # Create visual for each topic and concat them. 
    for i, topic in enumerate(topics): 
        chart_title = topic 
        data_topic = data[data["topic"] == topic] 

        # Base encoding. 
        chart = alt.Chart(data_topic) \
            .mark_bar(size=10) \
            .encode(
                x=alt.X(
                    f"{x}:Q", 
                    axis=alt.Axis(title="", titleFontSize=14, labelFontSize=10, labelAngle=0), 
                    scale=alt.Scale(domain=xlim), 
                ),
                y=alt.Y(
                    f"{y}:N", 
                    axis=alt.Axis(title="", titleFontSize=14, labelFontSize=10), 
                    sort=alt.EncodingSortField(field=f"{x}:Q", order="descending"), 
                ), 
                text=alt.Text(
                    f"{x}:Q", 
                    format=format_text, 
                ), 
                tooltip=[
                    alt.Tooltip(f"{x}:Q", title=x, format=format_text), 
                    alt.Tooltip(f"{y}:N", title=y), 
                ], 
            ) \
            .properties(title=chart_title, height=height, width=width) 


        # Construct the chart (row) x (column) dimension. 
        row |= chart.interactive() 
        if (
            (i > 0 and i % column == column - 1) or 
			(i == len(topics) - 1) 
        ): 
            charts &= row 
            row = alt.hconcat() 

    return charts 



# %%
def plot_dendrogram(model, **kwargs): 
    counts = np.zeros(model.children_.shape[0]) 
    n_samples = len(model.labels_) 

	# Count nodes. 
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count +=1
            else:
                current_count += counts[child_idx - n_samples] 
        counts[i] = current_count
    
	# Initiate the graph. 
    _, ax = plt.subplots(figsize = (8,8)) 
    ax.set_title("Hierarchical Topic Formation") 
    ax.set_xlabel("Topic") 

    linkage_matrix = np.column_stack([model.children_, model.distances_, counts]).astype(float) 
    dendrogram(linkage_matrix, **kwargs) 
    plt.show() 



# %%
def plot_umap(mapper, headline_id:np.array, latent_feature:np.array): 
	height, width = 400, 500 

	# Get the topic label. 
	latent_topic = np.argmax(latent_feature, axis=1) 
	hover_topics = pd.DataFrame(data={"headline_id": headline_id, "topic": latent_topic}) 

	# Plot. 
	umap.plot.output_notebook() 
	plot_umap = umap.plot.interactive(
		mapper, labels=latent_topic, hover_data=hover_topics, point_size=5, height=height, width=width
	) 
	umap.plot.show(plot_umap) 



# %%
def plot_correlation(data, x:str, y:str, xlim:tuple=(0,4), ylim:tuple=(0,4), format_text:str=".2f"): 
    height, width = 300, 400
    chart_title = "Correlation Between (True) & (Pred)" 

    # Base encoding. 
    chart = alt.Chart(data) \
        .mark_point(opacity=1) \
        .encode(
            x=alt.X(
                f"{x}:Q", 
                axis=alt.Axis(title=x, titleFontSize=14, labelFontSize=10, labelAngle=0), 
				scale=alt.Scale(domain=xlim), 
            ),
            y=alt.Y(
                f"{y}:Q", 
                axis=alt.Axis(title=y, titleFontSize=14, labelFontSize=10), 
				scale=alt.Scale(domain=ylim), 
            ), 
            tooltip=[
                alt.Tooltip(f"{x}:Q", title=x, format=format_text), 
                alt.Tooltip(f"{y}:Q", title=y, format=format_text), 
            ], 
        ) \
        .properties(title=chart_title, height=height, width=width) 

    chart += chart.transform_regression(x, y).mark_line(color="red") 
    return chart.interactive() 



# %% 
def plot_discre_dist(data, x:str, format_text:str=".2f"): 
	height, width = 50, 300 
	chart_title = x.replace("_", " ") 

	# Base encoding. 
	chart = alt.Chart(data[x].value_counts(normalize=True).reset_index(drop=False)) \
		.mark_bar(size=50) \
		.encode(
			x=alt.X(
				f"sum({x}):Q", 
				axis=alt.Axis(title="", titleFontSize=14, labelFontSize=10, labelAngle=0), 
				scale=alt.Scale(domain=[0,1]), 
			),
			color=alt.Color(
				f"index:N", 
				scale=alt.Scale(scheme="blues", reverse=False),
                legend=alt.Legend(title="Label categories", direction="vertical"), 
			), 
			tooltip=[
				alt.Tooltip(f"{x}:Q", title=x, format=format_text), 
				alt.Tooltip(f"index:N", title="categories"), 
			], 
		) \
		.properties(title=chart_title, height=height, width=width) 

	return chart 



# %% 
def plot_multiverse_analysis(data, x:str, y:str, err_minmax:tuple, xlim:list=[0,1.2], format_text:str=".3f"): 
	height, width = 400, 800 
	chart_title = "Multiverse Analysis Result (95% confidence interval)" 
	sort_experiment = data[y].to_list() 

	# Base encoding. 
	base = alt.Chart(data) \
		.encode(
			x=alt.X(
				f"{x}:Q", 
				axis=alt.Axis(title=x, titleFontSize=14, labelFontSize=10, labelAngle=0), 
				scale=alt.Scale(domain=xlim), 
			),
			y=alt.Y(
				f"{y}:N", 
				axis=alt.Axis(title=y, titleFontSize=14, labelFontSize=10, labelAngle=0), 
				sort=sort_experiment, 
			),
		) \
		.properties(title=chart_title, height=height, width=width) 

	chart = base \
		.mark_point(size=100, filled=True, color="black") \
		.encode(
			tooltip=[
				alt.Tooltip(f"{x}:Q", title=x, format=format_text), 
				alt.Tooltip(f"{y}:N", title="component"), 
			], 
		)

	errorbars = base \
		.mark_errorbar() \
		.encode(
			x=alt.X(f"{err_minmax[0]}:Q", title=""), 
			y=alt.Y(f"{y}:N", sort=sort_experiment), 
			x2=alt.X2(f"{err_minmax[1]}:Q", title=""), 
		) 

	return (chart + errorbars).interactive() 
