# Load required packages
library(tidyverse)
library(ape)
library(ggtree)

# Parse command line arguments
args <- commandArgs(trailingOnly = TRUE)
subtree_file <- args[1]
pairwise_file <- args[2]


# Load the pairwise file
pairwise_df <- read.csv(pairwise_file)

# Read the Newick string into a phylogenetic tree object
phylo_tree_new <- read.tree(subtree_file)


# Fortify the tree data to extract node information, including bootstrap values
tree_data_new <- fortify(phylo_tree_new, ladderize = FALSE,branch.length="none")

# Extract both digits and words after '->' in C_Map_1 and C_Map_2
pairwise_df <- pairwise_df %>%
  mutate(C_Map_1 = str_extract_all(C_Map_1, "(?<=->)[\\w]+"),
         C_Map_2 = str_extract_all(C_Map_2, "(?<=->)[\\w]+"))


# Annotate Char_1 and Char_2 with transitions, replacing "->" with "to"
pairwise_df <- pairwise_df %>%
  mutate(
    Char_1_annotated = case_when(
      grepl("->", Transition_1) ~ paste0(Char_1, " ", gsub("->", " to ", Transition_1)),
      TRUE ~ Char_1
    ),
    Char_2_annotated = case_when(
      grepl("->", Transition_2) ~ paste0(Char_2, " ", gsub("->", " to ", Transition_2)),
      TRUE ~ Char_2
    )
  )

tree_plot_new <- ggtree(phylo_tree_new, ladderize = FALSE, branch.length = "none") +
  geom_tiplab() +
  geom_nodelab(hjust = 0, vjust = -1.0, colour = "black") +
  # geom_tree(scale = 1.5) + theme_tree()
  geom_tree(color = "black", linewidth = 0.5) + # Make entire tree black
  scale_color_identity() # Use specified colors directly
  scale_y_reverse()


# Initialize data frames to aggregate node and tip annotations
node_annotations <- data.frame(node = character(), label = character(), color = character(), count = integer())
tip_annotations <- data.frame(tip = character(), label = character(), color = character(), count = integer())

# Aggregate annotations from all rows
for (i in seq_len(nrow(pairwise_df))) {
  # Process Char_1 annotations
  char1_nodes <- pairwise_df$C_Map_1[[i]]
  char1_label <- pairwise_df$Char_1_annotated[i]
  char1_counts <- table(char1_nodes)
  
  for (node in names(char1_counts)) {
    node_annotations <- rbind(node_annotations, data.frame(
      node = node,
      label = char1_label,
      color = "red",
      count = as.integer(char1_counts[node]),
      stringsAsFactors = FALSE
    ))
  }
  
  # Process Char_2 annotations
  char2_nodes <- pairwise_df$C_Map_2[[i]]
  char2_label <- pairwise_df$Char_2_annotated[i]
  char2_counts <- table(char2_nodes)
  
  for (node in names(char2_counts)) {
    node_annotations <- rbind(node_annotations, data.frame(
      node = node,
      label = char2_label,
      color = "blue",
      count = as.integer(char2_counts[node]),
      stringsAsFactors = FALSE
    ))
  }
}


# Summarize counts for each node and label
node_annotations_agg <- node_annotations %>%
  group_by(node, label, color) %>%
  summarise(count = sum(count), .groups = "drop")

# Merge with tree data to get coordinates and tip info
merged_node_data <- node_annotations_agg %>%
  left_join(tree_data_new %>% select(label, x, y, isTip), by = c("node" = "label")) %>%
  mutate(
    formatted_label = paste0(label, " (", count, "x)")
  )

# Split into node and tip data
node_data <- merged_node_data %>% filter(!isTip)
tip_data <- merged_node_data %>% filter(isTip)

# Create the base tree plot
tree_plot_new <- ggtree(phylo_tree_new, ladderize = FALSE, branch.length = "none") +
  geom_tiplab() +
  geom_nodelab(hjust = 0, vjust = -1.0, colour = "black") +
  geom_tree(color = "black", linewidth = 0.5) +
  scale_color_identity() +
  scale_y_reverse()

# Add Char_1 node annotations with specific positioning
if (nrow(node_data %>% filter(color == "blue")) > 0) {
  tree_plot_new <- tree_plot_new +
    geom_nodelab(
      data = node_data %>% filter(color == "blue"),
      aes(label = formatted_label, color = color),
      vjust = -3.5, hjust = 1.2,  # Adjusted for Char_1
    )
}

# Add Char_2 node annotations with specific positioning
if (nrow(node_data %>% filter(color == "red")) > 0) {
  tree_plot_new <- tree_plot_new +
    geom_nodelab(
      data = node_data %>% filter(color == "red"),
      aes(label = formatted_label, color = color),
      vjust = -1.5, hjust = 1.2,  # Adjusted for Char_2
    )
}

# Add Char_1 tip annotations with specific positioning
if (nrow(tip_data %>% filter(color == "blue")) > 0) {
  tree_plot_new <- tree_plot_new +
    geom_tiplab(
      data = tip_data %>% filter(color == "blue"),
      aes(label = formatted_label, color = color),
       vjust = -3, hjust = -0.2,  # Adjusted for Char_1
    )
}

# Add Char_2 tip annotations with specific positioning
if (nrow(tip_data %>% filter(color == "red")) > 0) {
  tree_plot_new <- tree_plot_new +
    geom_tiplab(
      data = tip_data %>% filter(color == "red"),
      aes(label = formatted_label, color = color),
       vjust = -1.5, hjust = -0.2,  # Adjusted for Char_2
    )
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


draw_parallel_lines <- function(tree_plot, node_n, num_annotations, color, 
                                line_spacing = 0.1, tip_offset = -0.3, internal_offset = 0.3, 
                                y_start = NULL) {
  # Fetch node coordinates dynamically
  current_node_coords <- tree_data_new %>% filter(label == node_n)
  parent_node_coords <- tree_data_new %>% filter(node == current_node_coords$parent)
  
  if (nrow(current_node_coords) == 1 && nrow(parent_node_coords) == 1) {
    x_start <- parent_node_coords$x
    x_end <- current_node_coords$x

    for (i in 0:(num_annotations - 1)) {
  # Determine y-coordinate based on the starting point
  if (!is.null(y_start)) {
    # Separate logic for tip and internal nodes when y_start is provided
    is_tip <- current_node_coords$isTip
    
    if (is_tip) {
      # Tip node: lines go downward
      y_line <- y_start - i * line_spacing
    } else {
      # Internal node: lines go upward
      y_line <- y_start + i * line_spacing
    }
  } 
       
      # Add line annotation
      tree_plot <- tree_plot + 
        annotate("segment", x = x_start, xend = x_end, y = y_line, yend = y_line, 
                 color = color, linetype = "solid", linewidth = 0.6)
    }
  }
  
  return(tree_plot)
}

# Initialize a list to store y-coordinates for Char_1 by node
char1_y_positions <- list()

# Loop to draw lines for Char_1 and store node-specific y-coordinates
for (j in seq_len(nrow(annotation_counts))) {
  node_n <- annotation_counts$node[j]
  num_annotations <- annotation_counts$count[j]
  line_color <- annotation_counts$color[j]

  
    if (annotation_counts$source[j] == "Char_1") {
    # Determine base y position based on node type (tip or internal)
    is_tip <- tree_data_new %>% filter(label == node_n) %>% pull(isTip)
    y_base <- if (is_tip) {
      tree_data_new %>% filter(label == node_n) %>% pull(y) - 0.1  # Tip nodes
    } else {
      tree_data_new %>% filter(label == node_n) %>% pull(y) + 0.1    # Internal nodes
    
    }
    
    # Draw lines for Char_1
    tree_plot_new <- draw_parallel_lines(tree_plot_new, node_n = node_n, 
                                         num_annotations = num_annotations, 
                                         color = line_color, 
                                         y_start = y_base)
    
    # Store the y-coordinate for the last line plotted at this node
    if (is_tip) {
      # For tip nodes: lines go downward, subtract from y_base
      last_y <- y_base - (num_annotations - 1) * 0.1
    } else {
      # For internal nodes: lines go upward, add to y_base
      last_y <- y_base + (num_annotations - 1) * 0.1
    }
    
    # Store the last_y for this node in char1_y_positions
    char1_y_positions[[node_n]] <- last_y

  }
}

# Loop to draw lines for Char_2 using Char_1 positions as the base
for (j in seq_len(nrow(annotation_counts))) {
  node_n <- annotation_counts$node[j]
  num_annotations <- annotation_counts$count[j]
  line_color <- annotation_counts$color[j]

  if (annotation_counts$source[j] == "Char_2") {
    # Retrieve y-coordinate from Char_1
    y_base <- char1_y_positions[[node_n]]
    
    # Determine offsets based on node type
    is_tip <- tree_data_new %>% filter(label == node_n) %>% pull(isTip)
    if (is_tip) {
      y_base <- y_base - 0.1  # Adjust further down for tips
    } else {
      y_base <- y_base + 0.1  # Slight upward shift for internal nodes
    }
    
    # Draw lines for Char_2
    tree_plot_new <- draw_parallel_lines(tree_plot_new, node_n = node_n, 
                                         num_annotations = num_annotations, 
                                         color = line_color, 
                                         y_start = y_base)
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

# Add colored branches
tree_plot_new <- tree_plot_new + 
  geom_tree(color = "black", size = 1) +  # Make entire tree black
  scale_color_identity()  # Use specified colors directly

print(tree_plot_new)
ggsave("images/viz2.png", plot = tree_plot_new, width = 12, height = 8, dpi = 300)
