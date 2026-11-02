# Load required packages
library(tidyverse)
library(ape)
library(ggtree)

# Parse command line arguments
args <- commandArgs(trailingOnly = TRUE)
subtree_file <- args[1]
pairwise_file <- args[2]

# Load the pairwise file and tree
pairwise_df <- read.csv(pairwise_file)
phylo_tree_new <- read.tree(subtree_file)
tree_data_new <- fortify(phylo_tree_new, ladderize = FALSE, branch.length = "none")

# Extract the destinations of the character-state mappings.
pairwise_df <- pairwise_df %>%
  mutate(
    C_Map_1 = str_extract_all(C_Map_1, "(?<=->)[\\w]+"),
    C_Map_2 = str_extract_all(C_Map_2, "(?<=->)[\\w]+")
  ) %>%
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

# Font sizes doubled: geom_tiplab / geom_nodelab default is ~3.88, so use ~7.76.
tree_plot_new <- ggtree(phylo_tree_new, ladderize = FALSE, branch.length = "none") +
  geom_tiplab(size = 7.76) +
  geom_nodelab(hjust = 0, vjust = -1.0, colour = "black", size = 7.76) +
  geom_tree(color = "black", linewidth = 0.5) +
  scale_color_identity() +
  scale_y_reverse()

# ============================================================
# COLLECT LABELS AND ASSIGN COLORS
# ============================================================
label_entries <- data.frame(
  node = character(), source = character(), 
  annotation_key = character(), count = integer()
)

for (i in seq_len(nrow(pairwise_df))) {
  for (entry in list(
    list(counts = table(pairwise_df$C_Map_1[[i]]), source = "Char_1", label = pairwise_df$Char_1_annotated[i]),
    list(counts = table(pairwise_df$C_Map_2[[i]]), source = "Char_2", label = pairwise_df$Char_2_annotated[i])
  )) {
    if (length(entry$counts) > 0) {
      label_entries <- rbind(label_entries, data.frame(
        node = names(entry$counts), source = entry$source,
        annotation_key = entry$label, count = as.integer(entry$counts)
      ))
    }
  }
}

# Aggregate identical transitions at the same node
label_entries <- label_entries %>%
  group_by(node, source, annotation_key) %>%
  summarise(count = sum(count), .groups = "drop")

# Assign colors based on rank of unique annotations per node.
# 1st = red/blue, 2nd = green/yellow, 3rd = purple/orange
label_entries <- label_entries %>%
  arrange(node, factor(source, levels = c("Char_1", "Char_2")), annotation_key) %>%
  group_by(node, source) %>%
  mutate(source_rank = row_number()) %>%
  ungroup() %>%
  mutate(
    color = case_when(
      source == "Char_1" & source_rank == 1 ~ "red",
      source == "Char_2" & source_rank == 1 ~ "blue",
      source == "Char_1" & source_rank == 2 ~ "#00B050", # Green
      source == "Char_2" & source_rank == 2 ~ "#FFC000", # Yellow
      source == "Char_1" & source_rank == 3 ~ "#800080", # Purple
      source == "Char_2" & source_rank == 3 ~ "#FF8C00", # Orange
      TRUE ~ "black"
    ),
    annotation_label = paste0(annotation_key, " (", count, "x)")
  )

# Derive annotation counts directly from the updated label_entries
annotation_counts <- label_entries %>%
  group_by(node, source, color) %>%
  summarise(count = sum(count), .groups = "drop")

# ============================================================
# ADAPTIVE LINE SPACING
# ============================================================
adaptive_line_spacing <- function(node_n, normal_spacing = 0.1,
                                  compression_threshold = 8,
                                  fraction = 0.90, default_height = 1) {
  node_row <- tree_data_new %>% filter(label == node_n)
  if (nrow(node_row) != 1) return(normal_spacing)

  total_annotations <- sum(annotation_counts$count[annotation_counts$node == node_n])
  if (total_annotations <= compression_threshold) return(normal_spacing)

  node_y <- node_row$y
  is_tip <- node_row$isTip
  tree_y <- tree_data_new %>% filter(isTip) %>% pull(y)
  distinct_y <- sort(unique(tree_y[is.finite(tree_y)]))
  lower <- distinct_y[distinct_y < node_y]
  upper <- distinct_y[distinct_y > node_y]

  directional_gap <- if (is_tip) {
    if (length(lower)) node_y - max(lower) else NA_real_
  } else {
    if (length(upper)) min(upper) - node_y else NA_real_
  }

  available_gap <- if (!is.na(directional_gap)) directional_gap else default_height / fraction
  min(normal_spacing, (fraction * available_gap) / total_annotations)
}

# ============================================================
# DRAW PARALLEL LINES
# ============================================================
draw_parallel_lines <- function(tree_plot, node_n, num_annotations, color,
                                line_spacing = 0.1, y_start = NULL) {
  current_node_coords <- tree_data_new %>% filter(label == node_n)
  parent_node_coords <- tree_data_new %>% filter(node == current_node_coords$parent)
  if (nrow(current_node_coords) != 1 || nrow(parent_node_coords) != 1) return(tree_plot)

  for (i in seq_len(num_annotations)) {
    is_tip <- current_node_coords$isTip
    y_line <- if (is_tip) {
      y_start - (i - 1) * line_spacing
    } else {
      y_start + (i - 1) * line_spacing
    }
    tree_plot <- tree_plot +
      annotate("segment", x = parent_node_coords$x, xend = current_node_coords$x,
               y = y_line, yend = y_line, color = color,
               linetype = "solid", linewidth = 0.6)
  }
  tree_plot
}

# ============================================================
# PLACE LINES (Simplified logic tracking the last y per node)
# ============================================================
line_y_positions <- list()
last_y_per_node <- list()

# Ensure deterministic order for the blocks
annotation_counts <- annotation_counts %>%
  arrange(node, factor(source, levels = c("Char_1", "Char_2")), color)

for (j in seq_len(nrow(annotation_counts))) {
  node_n <- annotation_counts$node[j]
  num_annotations <- annotation_counts$count[j]
  line_color <- annotation_counts$color[j]
  source_j <- annotation_counts$source[j]
  key <- paste0(source_j, "_", line_color)

  node_row <- tree_data_new %>% filter(label == node_n)
  if (nrow(node_row) != 1) next
  
  is_tip <- node_row$isTip
  node_y <- node_row$y
  line_spacing <- adaptive_line_spacing(node_n)

  # If it's the first block at this node, start at the node.
  # If it's a subsequent block, start one line_spacing away from the previous block's end.
  if (is.null(last_y_per_node[[node_n]])) {
    y_base <- if (is_tip) node_y - line_spacing else node_y + line_spacing
  } else {
    prev_end <- last_y_per_node[[node_n]]
    y_base <- if (is_tip) prev_end - line_spacing else prev_end + line_spacing
  }

  tree_plot_new <- draw_parallel_lines(
    tree_plot_new, node_n, num_annotations, line_color,
    line_spacing = line_spacing, y_start = y_base
  )

  source_positions <- if (is_tip) {
    y_base - (seq_len(num_annotations) - 1) * line_spacing
  } else {
    y_base + (seq_len(num_annotations) - 1) * line_spacing
  }

  if (is.null(line_y_positions[[node_n]])) line_y_positions[[node_n]] <- list()
  line_y_positions[[node_n]][[key]] <- source_positions

  # Store the final y-position of this block so the next block can chain off it
  last_y_per_node[[node_n]] <- if (is_tip) {
    y_base - (num_annotations - 1) * line_spacing
  } else {
    y_base + (num_annotations - 1) * line_spacing
  }
}

# ============================================================
# ASSIGN LABEL Y-POSITIONS (ANCHOR TO TOP/BOTTOM OF BLOCKS)
# ============================================================
label_entries$label_y <- NA_real_
label_entries$vjust_val <- 0.5

for (node_n in unique(label_entries$node)) {
  idx <- which(label_entries$node == node_n)
  if (length(idx) == 0) next
  
  node_row <- tree_data_new %>% filter(label == node_n)
  if (nrow(node_row) != 1) next
  is_tip <- node_row$isTip
  
  # Ensure deterministic order (Red, Blue, Green, Yellow...)
  color_order <- c("red", "blue", "#00B050", "#FFC000", "#800080", "#FF8C00", "black")
  idx <- idx[order(match(label_entries$color[idx], color_order))]
  
  for (k in seq_along(idx)) {
    i <- idx[k]
    source_i <- label_entries$source[i]
    color_i <- label_entries$color[i]
    key <- paste0(source_i, "_", color_i)
    
    y_positions <- line_y_positions[[node_n]][[key]]
    if (!is.null(y_positions)) {
      
      if (is_tip) {
        # Tips grow downwards (smaller Y is lower)
        if (k %% 2 == 1) {
          # Odd blocks (1st, 3rd): Anchor at bottom of block, text grows up
          label_entries$label_y[i] <- min(y_positions)
          label_entries$vjust_val[i] <- 1 
        } else {
          # Even blocks (2nd, 4th): Anchor at top of block, text grows down
          label_entries$label_y[i] <- max(y_positions)
          label_entries$vjust_val[i] <- 0 
        }
      } else {
        # Internal nodes grow upwards (larger Y is higher)
        if (k %% 2 == 1) {
          # Odd blocks: Anchor at top of block, text grows down
          label_entries$label_y[i] <- max(y_positions)
          label_entries$vjust_val[i] <- 0 
        } else {
          # Even blocks: Anchor at bottom of block, text grows up
          label_entries$label_y[i] <- min(y_positions)
          label_entries$vjust_val[i] <- 1 
        }
      }
      
    }
  }
}

# ============================================================
# PLOT LABELS
# ============================================================
node_geometry <- tree_data_new %>% select(label, node, parent, isTip, x)
parent_geometry <- tree_data_new %>% select(node, parent_x = x)

label_entries <- label_entries %>%
  left_join(node_geometry, by = c("node" = "label")) %>%
  left_join(parent_geometry, by = c("parent" = "node")) %>%
  mutate(internal_label_x = if_else(is.na(parent_x), x, parent_x - 0.08)) %>%
  filter(!is.na(label_y))

# Tip annotations receive their own lane to the right of all species names.
# Resolve labels vertically in that lane so nearby tips cannot print over each
# other or over the coloured branch blocks.
tip_label_lane_x <- max(tree_data_new$x) + 0.85
tip_label_min_gap <- 0.42
# Tip labels use a fixed lane outside the tree, while retaining the y-coordinate
# of their own coloured line block. This keeps each label visually associated
# with its annotation instead of separating it through a global reflow.
tip_label_lane_x <- max(tree_data_new$x) + 2.5
label_entries$tip_label_y <- label_entries$label_y
label_entries$tip_label_x <- if_else(label_entries$isTip, tip_label_lane_x, NA_real_)

tip_indices <- which(label_entries$isTip)
if (length(tip_indices) > 1) {
  ordered_tip_indices <- tip_indices[order(label_entries$label_y[tip_indices])]
  resolved_y <- label_entries$label_y[ordered_tip_indices]
  for (i in 2:length(resolved_y)) {
    resolved_y[i] <- max(resolved_y[i], resolved_y[i - 1] + tip_label_min_gap)
  }
  label_entries$tip_label_y[ordered_tip_indices] <- resolved_y
}

label_internal <- label_entries %>% filter(!isTip)
label_tips <- label_entries %>% filter(isTip)

if (nrow(label_internal) > 0) {
  tree_plot_new <- tree_plot_new +
    geom_text(data = label_internal,
              aes(x = internal_label_x, y = label_y,
                  label = annotation_label, color = color),
              # Use the calculated vjust to push text away from the lines
              vjust = label_internal$vjust_val,
              hjust = 1, size = 7.76, inherit.aes = FALSE) +
    scale_color_identity()
}
if (nrow(label_tips) > 0) {
  tree_plot_new <- tree_plot_new +
    geom_text(data = label_tips,
              aes(x = tip_label_x, y = tip_label_y,
                  label = annotation_label, color = color),
              hjust = 0, vjust = 0.5, size = 7.76, inherit.aes = FALSE) +
    scale_color_identity()
}
# Calculate limits and preserve the original rendering and labels.
min_x <- min(tree_data_new$x)
max_x <- max(tree_data_new$x)
min_y <- min(tree_data_new$y, label_entries$tip_label_y, na.rm = TRUE)
max_y <- max(tree_data_new$y, label_entries$tip_label_y, na.rm = TRUE)
margin_x <- 5
margin_x <- 4.5
margin_y <- 1.5

tree_plot_new <- tree_plot_new +
  scale_x_continuous(limits = c(min_x - margin_x, max_x + margin_x)) +
  scale_y_reverse(limits = c(max_y + margin_y, min_y - margin_y)) +
  geom_tree(color = "black", size = 1) +
  scale_color_identity()
print(tree_plot_new)

# Save directly to the images/ folder for the GitHub app to retrieve
ggsave("images/viz2.png", plot = tree_plot_new, width = 24, height = 20, dpi = 300)