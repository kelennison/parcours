# Parcours: Correlated Evolution Analysis
Live Web App: https://parcours.onrender.com/

## 🔬 What is Parcours? (Scientific Background)
Parcours (PARsimonious CO-occURrenceS) is a computational framework and web application designed to detect correlated evolution among pairs of discrete characters, given a phylogenetic tree.

**Why use Parsimony?**
Standard methods for studying evolution, such as Maximum Likelihood or Bayesian approaches, require a predefined model of evolution. However, in many biological scenarios, a reasonable model of evolutionary rate is unavailable, or the rates of change are highly heterogeneous across different lineages. In these cases, the principle of parsimony—which states that the evolutionary path requiring the fewest number of events is the most likely—is a more appropriate starting point.

**How it Works**
Instead of forcing a single ancestral state reconstruction, Parcours attempts to avoid bias by utilizing the entire set of possible parsimonious reconstructions.
* **Ancestral States:** The software uses Sankoff’s algorithm to compute all most parsimonious assignments of ancestral states for each character to the internal nodes of the phylogeny.
* **Transition Events:** It identifies all specific state transition events (e.g., absent → present) along the branches of the tree.
* **Correlation:** The correlation between two events is determined by their co-occurrence patterns across all possible parsimonies. This is quantified using the weighted Jaccard index (also known as the Ruzicka index), which measures the overlap of these events while normalizing for their independent occurrences.

Parcours was originally developed to study the correlated evolution of vocalizations and morphological characters in the Felidae (cat) family, but it can be applied to any discrete character dataset.

## 🚀 How to Use the Web App
The Parcours web app provides a user-friendly, interactive pipeline that takes you from raw data to publication-ready phylogenetic visualizations.

### Step 1: Upload Your Data
On the home screen, upload two required files:
* **Extant State File (.csv):** A CSV containing the species and their observed character states (e.g., 0 for absent, 1 for present).
* **Phylogenetic Tree File:** A Newick (.nh, .tree) or NEXUS (.nex, .nexus) file. *Note: NEXUS files are automatically converted to Newick on the fly.*

Click **"Run Analysis"**. The backend will compute all parsimonies, calculate the correlations between all character pairs, and generate downloadable result files (including `pairwise.csv`).

### Step 2: Proceed to Visualization
Once the analysis finishes, click **"Proceed to Visualize Analysis"**. This will load your results into the interactive dashboard.

### Step 3: Filter and Select Annotations
* **Adjust the Correlation Threshold Slider:** By default, it is set to 0.25. Move it higher to filter out weak correlations and focus only on the most significant evolutionary events.
* **Select Annotations:** Use the dropdown menus to select a pair of characters. You can check the boxes to include up to **four** annotations simultaneously to overlay multiple sets of correlated events.

### Step 4: Generate the Tree Visualizations
Depending on your selection, the app will prompt you to generate a tree visualization:
* **Visualization 1:** Generates a standard tree for a single annotated branch.
* **Visualization 2:** Generates a tree for multiple correlated transitions. This script uses dynamic line spacing to stack parallel colored lines without overlap.

The R backend runs in the background and returns a high-resolution `.png` image directly to your screen.

### Step 5: Explore the Interactive Heatmap
Below the tree visualizations, you can generate an interactive **Node × Transition Heatmap** to see exactly where and how often transitions occurred.

#### How to Read the Heatmap
* **Y-Axis (Rows): Node / Evolutionary Position:** The rows represent the specific nodes on the phylogeny, ordered by their evolutionary structure (from root to tips), not alphabetically.
* **X-Axis (Columns): Transition (State → State):** The columns represent specific evolutionary changes. For example, a column labeled `4->2` means a change from state 4 to state 2.
* **Cells (Intersections):** The number inside a cell represents the **exact count** of how many times that specific transition occurred at that specific node for the selected characters.
* **Colors (Hue & Intensity):**
  * **Hue (Red, Blue, Yellow/Brown, Green):** Each color represents a different character pair you selected in Step 3.
  * **Intensity (Light to Dark):** Lighter colors indicate fewer occurrences; darker colors indicate higher frequencies. Empty cells (0 occurrences) are shown as light gray.

#### Answering Common Questions
**Q: How do I know which characters the heatmap is based on?**
You can find the character names in three places:
1. In the **blue info box** directly above the heatmap controls.
2. As the title of the **legends (colorbars)** on the right side of the chart.
3. By hovering your mouse over any colored cell to read the tooltip.

**Q: How do I interpret a transition 4 to 2? Is that one character changing from state 4 to 2? If so, which one?**
Yes. If you hover over a cell in the `4->2` column, the tooltip will tell you exactly which character it refers to (e.g., `Characters: A.Vestibule - A.SCC`). 
If the cell shows the number **2**, it means that for that specific character pair, the trait changed from state 4 to state 2 exactly **twice** on that specific branch/node of the evolutionary tree.

#### Interactivity & Filters
Because the heatmap is built using Plotly, it is fully interactive:
* **Hover** over any cell to see a detailed tooltip containing the exact Characters, Node, Transition, and Count.
* Use the **"Minimum occurrence"** filter to hide noise and only show transitions that happen multiple times (e.g., setting it to `2` will hide all cells with a count of `1`).
* Toggle **Log-scaled intensity** to compress high-frequency counts so that rarer transitions remain visible in the color scale.

## 📄 Citation
If you use this tool in your research, please cite the original paper:

Smith, B., Buonopane, R., Navarro-Martinez, C., Byun, S., & Patterson, M. (2021). Parcours: PARsimonious CO-occURrenceS. Fairfield University & Georgia State University.