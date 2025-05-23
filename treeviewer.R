# Load the necessary libraries
library(ggtree)
library(ape)
library(tidyverse)

# Parse command line arguments
args <- commandArgs(trailingOnly = TRUE)
newick_file <- args[1]  # Corrected variable name

# Read the Newick string into a phylogenetic tree object
phylo_tree <- read.tree(newick_file)  # Use corrected variable name

# Fortify the tree data to extract node information
tree_data <- fortify(phylo_tree, ladderize = FALSE)

# Plot the tree
tree_plot <- ggtree(phylo_tree, ladderize = FALSE) + 
  geom_tiplab() +           
  geom_nodelab(hjust = 0, vjust = 1.1, colour = "black") +
  scale_y_reverse()

# Calculate limits and set margins
min_x <- min(tree_data$x)
max_x <- max(tree_data$x)
margin_x <- 2.5

tree_plot <- tree_plot +
  scale_x_continuous(limits = c(min_x - margin_x, max_x + margin_x)) +
  geom_tree(color = "black", size = 1)

# Save and display
ggsave("Rplot.png", plot = tree_plot, width = 10, height = 8, dpi = 300)
print(tree_plot)