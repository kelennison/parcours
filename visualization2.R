# Install BiocManager if it isn't already installed
if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Set the Bioconductor version to 3.20
BiocManager::install(version = "3.20")

# Force install ggtree from Bioconductor
BiocManager::install("ggtree", force = TRUE)

# Force install tidyverse from CRAN if not already installed
if (!require("tidyverse", quietly = TRUE))
    install.packages("tidyverse", repos = "http://cran.us.r-project.org", dependencies = TRUE)

# Force install ape from CRAN if not already installed
if (!require("ape", quietly = TRUE))
    install.packages("ape", repos = "http://cran.us.r-project.org", dependencies = TRUE)

# Load necessary libraries
library(tidyverse)
library(ape)
library(ggtree)



# Load the CSV file with vocalizations and transitions
pairwise_file <- "assets/pw_phys.csv"
pairwise_df <- read_csv(pairwise_file)

# Define the Newick file path
newick_string <- "(((((((Wild_Cat_Lineage,Leopard_Cat_Lineage)7,((Puma,Jaguarundi)19,Cheetah)18)6,Lynx_Lineage)5,Ocelot_Lineage)4,Caracal_Lineage)3,Bay_Cat_Lineage)2,Panthera_Lineage)1;"

# Read the Newick tree from the file
phylo_tree_new <- read.tree(text = newick_string)

# Fortify the tree data to extract node information, including bootstrap values
tree_data_new <- fortify(phylo_tree_new, ladderize = FALSE)

# Extract both digits and words after '->' in C_Map_1 and C_Map_2
pairwise_df <- pairwise_df %>%
  mutate(C_Map_1 = str_extract_all(C_Map_1, "(?<=->)[\\w]+"),
         C_Map_2 = str_extract_all(C_Map_2, "(?<=->)[\\w]+"))

# Annotate Char_1 and Char_2 with transitions
pairwise_df <- pairwise_df %>%
  mutate(Char_1_annotated = case_when(
    Transition_1 == "2->3" ~ paste0(Char_1, " 2 to 3"),
    Transition_1 == "1->3" ~ paste0(Char_1, " 1 to 3"),
    TRUE ~ Char_1
  ),
  Char_2_annotated = case_when(
    Transition_2 == "2->3" ~ paste0(Char_2, " 2 to 3"),
    Transition_2 == "1->3" ~ paste0(Char_2, " 1 to 3"),
    TRUE ~ Char_2
  ))

# Plot the tree

tree_plot_new <- ggtree(phylo_tree_new,  ladderize = FALSE, branch.length = "none") + 
  geom_tiplab() +            
  geom_nodelab(hjust = 0, vjust = -1.0, colour = "black") +  
  #geom_tree(scale = 1.5) + theme_tree()
  geom_tree(color = "black", linewidth = 0.5 ) +  # Make entire tree black
  scale_color_identity()  # Use specified colors directly
scale_y_reverse() 



# Loop through pairwise_df to add node annotations showing transition and counts
for (i in seq_len(nrow(pairwise_df))) {
  char1_labels <- pairwise_df$Char_1_annotated[i]
  char2_labels <- pairwise_df$Char_2_annotated[i]
  
  # Count occurrences of nodes for Char_1 and Char_2
  char1_counts <- table(pairwise_df$C_Map_1[[i]])
  char2_counts <- table(pairwise_df$C_Map_2[[i]])
  
  # Add node labels for plotting with counts
  tree_plot_new <- tree_plot_new +
    geom_nodelab(aes(label = ifelse(label %in% names(char1_counts), 
                                    paste(char1_labels, "(", char1_counts[as.character(label)], "x)", sep = ""), "")), 
                 vjust = -3.5, hjust = 1.2, color = "red") +
    geom_nodelab(aes(label = ifelse(label %in% names(char2_counts), 
                                    paste(char2_labels, "(", char2_counts[as.character(label)], "x)", sep = ""), "")), 
                 vjust = -1.5, hjust = 1.2, color = "blue")
  
}

# Loop through pairwise_df to add tip labels showing transition and counts
for (i in seq_len(nrow(pairwise_df))) {
  char1_labels <- pairwise_df$Char_1_annotated[i]
  char2_labels <- pairwise_df$Char_2_annotated[i]
  
  # Loop through pairwise_df to add tip labels showing transition and counts
  tree_plot_new <- tree_plot_new +
    geom_tiplab(aes(label = ifelse(label %in% names(char1_counts), 
                                   paste(char1_labels, "(", char1_counts[as.character(label)], "x)", sep = ""), "")), 
                vjust = -3, hjust = 0, color = "red") +
    geom_tiplab(aes(label = ifelse(label %in% names(char2_counts), 
                                   paste(char2_labels, "(", char2_counts[as.character(label)], "x)", sep = ""), "")), 
                vjust = -1.5, hjust = 0, color = "blue")
  
}

# Create a new data frame to count annotations per node and their sources
annotation_counts <- data.frame(node = character(), count = integer(), source = character(), color = character())

# Loop through pairwise_df to add node annotations and their colors
for (i in seq_len(nrow(pairwise_df))) {
  char1_labels <- pairwise_df$Char_1_annotated[i]
  char2_labels <- pairwise_df$Char_2_annotated[i]
  
  char1_counts <- table(pairwise_df$C_Map_1[[i]])
  char2_counts <- table(pairwise_df$C_Map_2[[i]])
  
  # Add Char_1 annotations with red color
  for (label in names(char1_counts)) {
    existing_row <- annotation_counts %>% filter(node == label, source == "Char_1")
    if (nrow(existing_row) > 0) {
      annotation_counts$count[annotation_counts$node == label & annotation_counts$source == "Char_1"] <- 
        annotation_counts$count[annotation_counts$node == label & annotation_counts$source == "Char_1"] + char1_counts[label]
    } else {
      annotation_counts <- rbind(annotation_counts, data.frame(node = label, count = char1_counts[label], source = "Char_1", color = "red"))
    }
  }
  
  # Add Char_2 annotations with blue color
  for (label in names(char2_counts)) {
    existing_row <- annotation_counts %>% filter(node == label, source == "Char_2")
    if (nrow(existing_row) > 0) {
      annotation_counts$count[annotation_counts$node == label & annotation_counts$source == "Char_2"] <- 
        annotation_counts$count[annotation_counts$node == label & annotation_counts$source == "Char_2"] + char2_counts[label];
    } else {
      annotation_counts <- rbind(annotation_counts, data.frame(node = label, count = char2_counts[label], source = "Char_2", color = "blue"));
    }
  }
}

draw_parallel_lines <- function(tree_plot, node_n, num_annotations, 
                                line_spacing = 0.1, tip_offset = -0.2, internal_offset = -0.2, color = "black") {
  current_node_coords <- tree_data_new %>% filter(label == node_n)
  parent_node_coords <- tree_data_new %>% filter(node == current_node_coords$parent)
  
  if (nrow(current_node_coords) == 1 && nrow(parent_node_coords) == 1) {  
    x_start <- parent_node_coords$x  
    x_end <- current_node_coords$x    
    y_base <- current_node_coords$y
    
    # Check if the current node is a tip or not
    if (current_node_coords$isTip) {
      # For tip nodes, plot above the branch using tip_offset
      y_base <- y_base + tip_offset
    } else {
      # For internal nodes, plot below the branch using internal_offset
      y_base <- y_base - internal_offset
    }
    
    # Draw n-1 lines if num_annotations > 1
    if (num_annotations > 1) {
      for (i in 0:(num_annotations - 1)) {  # Adjust to n-1 lines
        y_line <- y_base - i * line_spacing 
        tree_plot <- tree_plot + 
          annotate("segment", x = x_start, xend = x_end, y = y_line, yend = y_line, 
                   color = color, linetype = "solid", linewidth = 0.6)
        
      }
    }
  }
  
  return(tree_plot)
}

# Variable to track the last plotted y position for Char_1
last_y_char_1 <- NULL

# Loop to draw lines based on the annotation counts for Char_1
for (j in seq_len(nrow(annotation_counts))) {
  node_n <- annotation_counts$node[j]
  num_annotations <- annotation_counts$count[j]
  line_color <- annotation_counts$color[j]
  
  if (annotation_counts$source[j] == "Char_1") {
    y_base <- tree_data_new %>% filter(label == node_n) %>% pull(y) - 0.1  # Starting y position for Char_1
    tree_plot_new <- draw_parallel_lines(tree_plot_new, node_n = node_n, 
                                         num_annotations = num_annotations, 
                                         color = line_color, 
                                         line_spacing = 0.1, 
                                         tip_offset = -0.3, 
                                         internal_offset = -0.2)  
    
    # Update last_y_char_1 for the next source
    last_y_char_1 <- y_base - (num_annotations - 1) * 0.1
  }
}

# Loop to draw lines based on the annotation counts for Char_2
for (j in seq_len(nrow(annotation_counts))) {
  node_n <- annotation_counts$node[j]
  num_annotations <- annotation_counts$count[j]
  line_color <- annotation_counts$color[j]
  
  if (annotation_counts$source[j] == "Char_2") {
    # Use the last y position from Char_1 as the starting point
    y_base <- last_y_char_1 - 0.1  # Offset from the last plotted y position for Char_1
    tree_plot_new <- draw_parallel_lines(tree_plot_new, node_n = node_n, 
                                         num_annotations = num_annotations, 
                                         color = line_color, 
                                         line_spacing = 0.1, 
                                         tip_offset = 0, 
                                         internal_offset = 0.3)
  }
}

# Calculate x and y limits based on the tree data
min_x <- min(tree_data_new$x)
max_x <- max(tree_data_new$x)
min_y <- min(tree_data_new$y)
max_y <- max(tree_data_new$y)

# Define margins for padding around the plot
margin_x <- 2.5  # Adjust as needed
margin_y <- 1  # Adjust as needed

# Set x-axis limits to fit the entire tree horizontally and reverse y-axis limits to fit vertically
tree_plot_new <- tree_plot_new +
  scale_x_continuous(limits = c(min_x - margin_x, max_x + margin_x)) +
  scale_y_reverse(limits = c(max_y + margin_y, min_y - margin_y))  # maintain y-axis reversal and add limits

# Assuming annotation_counts already has the nodes to color
# Get unique nodes from annotation_counts for Char_1 and Char_2
nodes_to_color <- unique(annotation_counts$node[annotation_counts$color == "red"])  # Adjust condition as needed
colors <- rep("blue", length(nodes_to_color))  # Define colors for each node

# Loop through the nodes to color based on annotations
for (i in seq_along(nodes_to_color)) {
  node_label <- nodes_to_color[i]
  color <- colors[i]
  
  # Get the current node coordinates
  current_node_coords <- tree_data_new %>% filter(label == node_label)
  
  if (nrow(current_node_coords) > 0) {
    # Get the parent node
    parent_node_coords <- tree_data_new %>% filter(node == current_node_coords$parent)
    
    if (nrow(parent_node_coords) > 0) {
      # Define the x and y coordinates for the segment
      x_start <- parent_node_coords$x  # Parent node x
      x_end <- current_node_coords$x    # Current node x
      y_value <- current_node_coords$y  # Use current node y for both y and yend
      
      # Add the segment to the plot
      tree_plot_new <- tree_plot_new +
        annotate("segment", x = x_start, xend = x_end, 
                 y = y_value, yend = y_value, 
                 color = color, linewidth = 0.6)  # Adjust size as needed
    }
  }
}





# Print the updated plot
print(tree_plot_new)
ggsave("images/viz2.png", plot = tree_plot_new, width = 12, height = 8, dpi = 300)
