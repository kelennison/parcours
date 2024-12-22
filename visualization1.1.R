# Load required packages
library(tidyverse)
library(ape)
library(ggtree)

# Parse command line arguments
args <- commandArgs(trailingOnly = TRUE)
subtree_file <- args[1]
pairwise_file <- args[2]

# Read the pairwise CSV data
pairwise_df <- read_csv(pairwise_file)

# Read the Newick string into a phylogenetic tree object
phylo_tree <- read.tree(subtree_file)

# Fortify the tree data to extract node information, including bootstrap values
tree_data <- fortify(phylo_tree)




# Annotate Char_1 and Char_2 with (-) or (+) based on transitions
pairwise_df <- pairwise_df %>%
  mutate(
    C_Map_1 = str_extract(C_Map_1, "(?<=->).*"), # Extract everything after '->'
    C_Map_2 = str_extract(C_Map_2, "(?<=->).*"), # Extract everything after '->'
    Char_1_annotated = case_when(
      Transition_1 == "1->0" ~ paste0(Char_1, "(-)"),
      Transition_1 == "0->1" ~ paste0(Char_1, "(+)"),
      TRUE ~ Char_1 # Keep Char_1 as is if no transition
    ),
    Char_2_annotated = case_when(
      Transition_2 == "1->0" ~ paste0(Char_2, "(-)"),
      Transition_2 == "0->1" ~ paste0(Char_2, "(+)"),
      TRUE ~ Char_2 # Keep Char_2 as is if no transition
    )
  )



# Plot the tree and bootstrap values without adjusting position
tree_plot <- ggtree(phylo_tree, ladderize = FALSE, branch.length = "none") +
  geom_tiplab() + # Tip labels for species
  geom_nodelab(hjust = 0) + # Bootstrap values
  scale_y_reverse() # Ensure y-axis is reversed

# Add node annotations for Char_1_annotated with fine-tuned positioning
tree_plot <- tree_plot +
  geom_nodelab(aes(label = pairwise_df$Char_1_annotated[match(label, pairwise_df$C_Map_1)]),
    vjust = -3, hjust = 1.5, color = "blue"
  ) # Directly use pairwise_df without filtering

# Add node annotations for Char_2_annotated with fine-tuned positioning
tree_plot <- tree_plot +
  geom_nodelab(aes(label = pairwise_df$Char_2_annotated[match(label, pairwise_df$C_Map_2)]),
    vjust = -1.5, hjust = 1.3, color = "red"
  ) # Directly use pairwise_df without filtering

# Add annotations for Char_1 near the corresponding bootstrap values
tree_plot <- tree_plot +
  geom_tiplab(aes(label = pairwise_df$Char_1[match(label, pairwise_df$C_Map_1)]),
    vjust = -3, hjust = 2, color = "blue"
  ) # Adjust vjust and hjust for better alignment1

# Add annotations for Char_2 near the corresponding bootstrap values
tree_plot <- tree_plot +
  geom_tiplab(aes(label = pairwise_df$Char_2[match(label, pairwise_df$C_Map_2)]),
    vjust = -1.5, hjust = 1.8, color = "red"
  )

# Calculate x and y limits based on the tree data
min_x <- min(tree_data$x)
max_x <- max(tree_data$x)
min_y <- min(tree_data$y)
max_y <- max(tree_data$y)

# Define margins for padding around the plot
margin_x <- 1 # Adjust as needed
margin_y <- 1 # Adjust as needed

# Set x-axis limits to fit the entire tree horizontally and reverse y-axis limits to fit vertically
tree_plot <- tree_plot +
  scale_x_continuous(limits = c(min_x - margin_x, max_x + margin_x)) +
  scale_y_reverse(limits = c(max_y + margin_y, min_y - margin_y)) # maintain y-axis reversal and add limits

# Print the plot with improved annotations
print(tree_plot)


ggsave("C:\\Users\\USER\\OneDrive\\Documents\\Hello World\\parcours-main\\viz1.png", plot = tree_plot, width = 10, height = 8, dpi = 300)
