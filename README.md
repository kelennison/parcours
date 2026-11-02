Parcours: Correlated Evolution Analysis
Live Web App: https://parcours.onrender.com/

🔬 What is Parcours? (Scientific Background)
Parcours (PARsimonious CO-occURrenceS) is a computational framework and web application designed to detect correlated evolution among pairs of discrete characters, given a phylogenetic tree.

Why use Parsimony?
Standard methods for studying evolution, such as Maximum Likelihood or Bayesian approaches, require a predefined model of evolution. However, in many biological scenarios, a reasonable model of evolutionary rate is unavailable, or the rates of change are highly heterogeneous across different lineages. In these cases, the principle of parsimony—which states that the evolutionary path requiring the fewest number of events is the most likely—is a more appropriate starting point.

How it Works
Instead of forcing a single ancestral state reconstruction, Parcours attempts to avoid bias by utilizing the entire set of possible parsimonious reconstructions.

Ancestral States: The software uses Sankoff’s algorithm to compute all most parsimonious assignments of ancestral states for each character to the internal nodes of the phylogeny.

Transition Events: It identifies all specific state transition events (e.g., absent → present) along the branches of the tree.

Correlation: The correlation between two events is determined by their co-occurrence patterns across all possible parsimonies. This is quantified using the weighted Jaccard index (also known as the Ruzicka index), which measures the overlap of these events while normalizing for their independent occurrences.

Parcours was originally developed to study the correlated evolution of vocalizations and morphological characters in the Felidae (cat) family, but it can be applied to any discrete character dataset.

🚀 How to Use the Web App
The Parcours web app provides a user-friendly, interactive pipeline that takes you from raw data to publication-ready phylogenetic visualizations.

Step 1: Upload Your Data
On the home screen, upload two required files:

Extant State File (.csv): A CSV containing the species and their observed character states (e.g., 0 for absent, 1 for present).

Phylogenetic Tree File: A Newick (.nh, .tree) or NEXUS (.nex, .nexus) file. Note: NEXUS files are automatically converted to Newick on the fly.

Click "Run Analysis". The backend will compute all parsimonies, calculate the correlations between all character pairs, and generate downloadable result files (including pairwise.csv).

Step 2: Proceed to Visualization
Once the analysis finishes, click "Proceed to Visualize Analysis". This will load your results into the interactive dashboard.

Step 3: Filter and Select Annotations
Adjust the Correlation Threshold Slider: By default, it is set to 0.25. Move it higher to filter out weak correlations and focus only on the most significant evolutionary events.

Select Annotations: Use the dropdown menus to select a pair of characters. You can also check "Include a second annotation" to overlay a second set of correlated events on the same tree.

Step 4: Generate the Tree Visualizations
Depending on your selection, the app will prompt you to generate a visualization:

Visualization 1: Generates a standard tree for a single annotated branch.

Visualization 2: Generates a tree for multiple correlated transitions. This script uses dynamic line spacing to stack parallel colored lines without overlap.

Colors are automatically assigned in pairs: Red/Blue (1st), Green/Yellow (2nd), and Purple/Orange (3rd).

The R backend runs in the background and returns a high-resolution .png image directly to your screen.

Step 5: Explore the Interactive Heatmap
At the bottom of the results page, you can generate an interactive Node × Transition Heatmap.

Filter by Character 1, Character 2, or Both.

Adjust the Minimum Occurrence to remove rare transitions.

Toggle Log-scaled intensity to prevent high-frequency events from washing out the color scale.

Hover over any cell to see the exact node, transition, and count.

📄 Citation
If you use this tool in your research, please cite the original paper:

Smith, B., Buonopane, R., Navarro-Martinez, C., Byun, S., & Patterson, M. (2021). Parcours: PARsimonious CO-occURrenceS. Fairfield University & Georgia State University.
