import networkx as nx
from pyvis.network import Network
import numpy as np
import math

# Configuration
MAX_SIGNALS_PER_CLUSTER = 25

def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def build_cluster_graph(clusters, threshold=0.55):
    G = nx.Graph()

    for cluster in clusters:
        cluster_id = cluster["cluster_id"]
        cluster_label = cluster["label"]
        signals = cluster["signals"]
        embeddings = cluster["embeddings"]
        total_signal_count = len(signals)

        # Sort signals by timestamp (most recent first)
        signals_with_embeddings = list(zip(signals, embeddings))
        signals_with_embeddings.sort(key=lambda x: x[0]["timestamp"], reverse=True)
        
        # Cap visible signals
        visible_signals = signals_with_embeddings[:MAX_SIGNALS_PER_CLUSTER]
        hidden_count = total_signal_count - len(visible_signals)

        # Add visible signal nodes
        for i, (s, emb) in enumerate(visible_signals):
            short_label = s["text"][:40] + "…"
            G.add_node(
                s["signal_id"],
                label="",  # Hide label for cleanliness
                title=s["text"],  # Full text on hover
                size=6,
                color="#8ecae6",
                physics=True,  # Enable physics for dragging
                shape='dot',  # Explicitly set shape to dot to minimize borders
                borderWidth=0,  # Remove outer circle
                borderWidthSelected=0
            )

        # Add signal-signal edges (only between visible signals and only strong connections)
        for i in range(len(visible_signals)):
            for j in range(i+1, len(visible_signals)):
                sim = cosine(visible_signals[i][1], visible_signals[j][1])
                if sim > 0.65:  # Higher threshold for cleaner graph
                    # Fade edge color for large clusters
                    edge_opacity = 1.0 if total_signal_count < 50 else 0.5 if total_signal_count < 100 else 0.3
                    edge_color = f"rgba(14, 17, 23, {edge_opacity})"
                    G.add_edge(
                        visible_signals[i][0]["signal_id"],
                        visible_signals[j][0]["signal_id"],
                        value=sim,
                        color=edge_color,
                        smooth=False  # Straight lines
                    )

        # Calculate logarithmic cluster node size based on total signal count
        # Formula: base_size + log_factor * log(1 + signal_count)
        base_size = 35
        log_factor = 15
        cluster_size = base_size + log_factor * math.log(1 + total_signal_count)
        
        # Add cluster anchor node
        cluster_node_id = f"cluster_{cluster_id}"
        G.add_node(
            cluster_node_id,
            label=cluster_label,
            title=f"{cluster_label} ({total_signal_count} signals)",
            size=cluster_size,
            color="#f4b000",
            font={"size": 18, "color": "white"},
            physics=True,  # Enable physics for dragging
            borderWidth=0,
            borderWidthSelected=0
        )

        # Connect cluster to visible signals
        # Fade edge color for large clusters
        edge_opacity = 1.0 if total_signal_count < 50 else 0.6 if total_signal_count < 100 else 0.4
        cluster_edge_color = f"rgba(244, 176, 0, {edge_opacity})"
        
        for s, emb in visible_signals:
            G.add_edge(
                cluster_node_id,
                s["signal_id"],
                value=0.9,
                color=cluster_edge_color,
                smooth=False  # Straight lines
            )
        
        # Add "+N more" collapsed node if there are hidden signals
        if hidden_count > 0:
            collapsed_node_id = f"collapsed_{cluster_id}"
            G.add_node(
                collapsed_node_id,
                label=f"+{hidden_count} more",
                title=f"This cluster has {hidden_count} more signals not shown in the graph.\nSelect the cluster below to view all {total_signal_count} signals.",
                size=12,
                color="#ff9500",
                font={"size": 14, "color": "white"},
                physics=True,
                borderWidth=0,
                borderWidthSelected=0,
                shape='box'
            )
            
            # Connect collapsed node to cluster hub
            G.add_edge(
                cluster_node_id,
                collapsed_node_id,
                value=0.9,
                color="#ff9500",
                smooth=False,
                dashes=True
            )

    # Cross-cluster edges
    for i in range(len(clusters)):
        for j in range(i+1, len(clusters)):
            if "centroid" in clusters[i] and "centroid" in clusters[j]:
                sim = cosine(clusters[i]["centroid"], clusters[j]["centroid"])
                if sim > 0.7:
                    G.add_edge(
                        f"cluster_{clusters[i]['cluster_id']}",
                        f"cluster_{clusters[j]['cluster_id']}",
                        value=sim,
                        color="#ff006e",
                        dashes=True,
                        smooth=False  # Straight lines
                    )

    net = Network(height="600px", bgcolor="#0e1117", font_color="white")
    net.from_nx(G)
    
    # Configure physics for initial layout only - will be disabled after stabilization
    net.set_options("""
    {
        "nodes": {
            "borderWidth": 0,
            "borderWidthSelected": 0,
            "chosen": {
                "node": false,
                "label": false
            },
            "font": {
                "strokeWidth": 0
            }
        },
        "interaction": {
            "hover": true,
            "hoverConnectedEdges": false,
            "selectConnectedEdges": false,
            "dragNodes": true,
            "dragView": true,
            "zoomView": true
        },
        "physics": {
            "enabled": true,
            "stabilization": {
                "enabled": true,
                "iterations": 200,
                "updateInterval": 25,
                "fit": true
            },
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 0.5
            },
            "solver": "barnesHut"
        }
    }
    """)
    
    # Add custom JavaScript for click-to-show-persistent-text and group movement
    custom_html = """
    <script type="text/javascript">
        var selectedNode = null;
        var physicsDisabled = false;
        
        // Disable physics after stabilization so nodes stay where moved
        network.once("stabilizationIterationsDone", function() {
            network.setOptions({ physics: { enabled: false } });
            physicsDisabled = true;
        });
        
        // When dragging a cluster node, move all connected signal nodes with it
        var dragStartPositions = {};
        var clusterStartPosition = {};
        var isDraggingCluster = false;
        
        network.on("dragStart", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                
                // Check if this is a cluster node
                if (nodeId.startsWith('cluster_')) {
                    isDraggingCluster = true;
                    // Store initial position of cluster
                    clusterStartPosition = network.getPositions([nodeId])[nodeId];
                    
                    // Get all connected signal nodes
                    var connectedNodes = network.getConnectedNodes(nodeId);
                    dragStartPositions = {};
                    
                    connectedNodes.forEach(function(connectedId) {
                        if (!connectedId.startsWith('cluster_')) {
                            dragStartPositions[connectedId] = network.getPositions([connectedId])[connectedId];
                        }
                    });
                } else {
                    // Dragging a signal node - allow independent movement
                    isDraggingCluster = false;
                }
            }
        });
        
        network.on("dragging", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                
                // If dragging a cluster, move connected signals
                if (isDraggingCluster && nodeId.startsWith('cluster_') && Object.keys(dragStartPositions).length > 0) {
                    var currentPos = network.getPositions([nodeId])[nodeId];
                    var dx = currentPos.x - clusterStartPosition.x;
                    var dy = currentPos.y - clusterStartPosition.y;
                    
                    // Move all connected signal nodes by the same offset
                    for (var connectedId in dragStartPositions) {
                        var oldPos = dragStartPositions[connectedId];
                        var newX = oldPos.x + dx;
                        var newY = oldPos.y + dy;
                        network.moveNode(connectedId, newX, newY);
                    }
                }
                // If dragging a signal node, it moves independently (default behavior)
            }
        });
        
        network.on("dragEnd", function(params) {
            // Clear drag state
            dragStartPositions = {};
            clusterStartPosition = {};
            isDraggingCluster = false;
        });
        
        network.on("click", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var node = network.body.data.nodes.get(nodeId);
                
                // Create persistent popup
                var popup = document.createElement('div');
                popup.id = 'node-popup';
                popup.style.position = 'fixed';
                popup.style.background = '#1e1e1e';
                popup.style.color = 'white';
                popup.style.padding = '15px';
                popup.style.borderRadius = '8px';
                popup.style.maxWidth = '400px';
                popup.style.border = '2px solid #f4b000';
                popup.style.zIndex = '10000';
                popup.style.top = '50%';
                popup.style.left = '50%';
                popup.style.transform = 'translate(-50%, -50%)';
                popup.style.boxShadow = '0 4px 20px rgba(0,0,0,0.5)';
                popup.innerHTML = '<strong>' + (node.label || 'Signal') + '</strong><br><br>' + 
                                 (node.title || 'No content') + 
                                 '<br><br><small style="color: #888;">Click anywhere to close</small>';
                
                // Remove existing popup if any
                var existing = document.getElementById('node-popup');
                if (existing) existing.remove();
                
                document.body.appendChild(popup);
                selectedNode = nodeId;
            } else {
                // Click on empty space - remove popup
                var popup = document.getElementById('node-popup');
                if (popup) popup.remove();
                selectedNode = null;
            }
        });
    </script>
    """
    
    try:
        net.write_html("cluster_graph.html")
        
        # Inject custom JavaScript into the generated HTML
        with open("cluster_graph.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Insert custom script before closing body tag
        html_content = html_content.replace("</body>", custom_html + "</body>")
        
        with open("cluster_graph.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
    except Exception as e:
        with open("cluster_graph.html", "w") as f:
            f.write(f"<html><body><h3>Cluster Graph (pyvis error: {e})</h3><p>Clusters: {len(clusters)}</p></body></html>")
