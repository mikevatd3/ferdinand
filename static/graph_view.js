fetch(endpoint)
    .then(response => response.json())
    .then(data => {
        const coms = buildComsSystem(data);
        drawGraph(data, coms);
    })
    .catch(error => console.error("error fetching data:", error));

const defaultColor = (node) => node.type === "phrase" ? PHRASE_COLOR : SENTENCE_COLOR;
const addClassName = (node) => node.type === "phrase" ? "phrase_node" : "sentence_node";

function buildUrl(node) {
    if (node.id[0] === "p") {
        return `/phrases/${node.id.slice(1)}`;
    } else if (node.id[0] === "s") {
        return `/sentences/${node.id.slice(1)}`;
    } else {
        console.log(`${node.id} is an invalid node id!`);
    }
}

function drawGraph(graph, coms) {
    let width = 1200,
        height = 525

    const svg = d3.select("#chart")
        .attr("viewBox", `0 0 ${width} ${height}`)

    // Simulation setup with forces
    let simulation = d3.forceSimulation(graph.nodes)
        .force("link", d3.forceLink(graph.edges).id(d => d.id))
        .force("charge", d3.forceManyBody().strength(-500))
        .force("center", d3.forceCenter(width / 2, height / 2));
    
    // Add lines for every link in the graphset
    const links = svg.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(graph.edges)
        .enter().append("line")
        .attr("id", (d) => `l-${d.source.id}-${d.target.id}`)
        .attr("stroke", "#272f3f")
        .attr("stroke-width", 2);
    
    // Add circles for every node in the graphset
    const nodes = svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(graph.nodes)
        .enter()
        .append("a")
        .attr("href", buildUrl)
        .append("circle")
        .attr("id", (d) => d.id)
        .attr("r", 8)
        .attr("color", defaultColor)
        .attr("class", addClassName)
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
        .on("mouseover", (_, obj) => coms[obj.id].handle("mouseover"))
        .on("mouseout", (_, obj) => coms[obj.id].handle("mouseout"))

    const labels = svg.append("g")
        .attr("class", "labels")
        .selectAll("text")
        .data(graph.nodes)
        .enter().append("text")
        .attr("x", 8)
        .attr("y", "0.31em")
        .attr("display", "none")
        .attr("id", (d) => `l-${d.id}`)
        .text(d => shortenSentence(d.words));

    // Define the drag behavior
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }

    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }

    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }

    // Update positions each tick
    simulation.on("tick", () => {
        nodes
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        labels
            .attr("x", d => d.x + 10)
            .attr("y", d => d.y - 5);

        links
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
          });
}

