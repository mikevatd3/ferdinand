
function shortenSentence(text) {
    if (text.length > 25) {
        return text.slice(0, 22) + "..."
    }
    return text
}

function wordWrap(text) {
    if (text.length > 25) {
        return text.slice(0, 22) + "..."
    }
    return text
}


class Label {
    constructor(id, words) {
        this.id = "l-" + id;
        this.words = words;
    }
    handle(event) {
        switch(event) {
            case "mouseover":
                d3.select(`#${this.id}`)
                  .text(this.words)
                  .style("font-size", "none")
                  .style("opacity", 1)
                  .attr("display", "inline")
                break;

            case "indirectOver":
                d3.select(`#${this.id}`)
                  .text(shortenSentence(this.words))
                  .style("opacity", 0.5)
                  .style("font-size", "smaller")
                  .attr("display", "inline")
                break;

            case "mouseout":
                d3.select(`#${this.id}`)
                  .style("font-size", "medium")
                  .attr("display", "none")
                break;
        }
    }
}

class Sentence {
    constructor(id, words) {
        this.id = id;
        this.label = new Label(id, words);
        this.parentLink = null;
        this.parent = null;
        this.childLinks = [];
        this.children = [];
        this.related = [];
    }
    handle(event) {
        switch (event) {
            case "mouseover":
                // First message the event out to linked objects
                this.label.handle("mouseover");
                this.children.forEach(child =>  child.handle("childOver"));
                this.childLinks.forEach(child =>  child.handle("childLinkOver"));
                if (this.parent) {this.parent.handle("parentOver")};
                if (this.parent) {this.parentLink.handle("parentLinkOver")};

                // Then handle the d3 stuff on the object itself
                d3.select(`#${this.id}`)
                  .attr("class", "selected_node")
                break;

            case "parentOver":
                this.label.handle("indirectOver");
                break;

            case "childOver":
                this.label.handle("indirectOver");
                break;

            case "relatedOver":
                break;
            
            case "mouseout":
                if (this.parent) {this.parent.handle("parentOut")};
                this.children.forEach(child => child.handle("childOut"));
                this.childLinks.forEach(child =>  child.handle("childLinkOut"));
                if (this.parentLink) {this.parentLink.handle("parentLinkOut")};
                // don't break!

            default:
                this.label.handle("mouseout");
                d3.select(`#${this.id}`)
                  .attr("class", "sentence_node")
                break;

        }
    }
}

class Phrase {
    constructor(id, words) {
        this.id = id;
        this.label = new Label(id, words);
        this.context = null;
        this.contextLink = null;
        this.definition = null;
        this.definitionLink = null;
        this.related = [];
    }
    handle(event) {
        switch (event) {
            case "mouseover":
                this.label.handle("mouseover");
                if (this.context) {this.context.handle("parentOver")};
                if (this.contextLink) {this.contextLink.handle("parentLinkOver")};
                if (this.definition) {this.definition.handle("childOver")};
                if (this.definitionLink) {
                    this.definitionLink.handle("childLinkOver")
                };

                d3.select(`#${this.id}`)
                  .attr("class", "selected_node")
                break;

            case "parentOver":
                this.label.handle("indirectOver")
                break;

            case "childOver":
                this.label.handle("indirectOver")
                break;

            case "relatedOver":
                break;

            default:
                this.label.handle("mouseout")
                if (this.contextLink) {this.contextLink.handle("parentLinkOut")};
                if (this.context) {this.context.handle("parentOut")};
                if (this.definition) {this.definition.handle("childOut")};
                if (this.definitionLink) {this.definitionLink.handle("childLinkOut")};

                d3.select(`#${this.id}`)
                  .attr("class", "phrase_node")
        }
    }
}


function buildNode(node) {
    switch (node.type) {
        case 'phrase':
            return new Phrase(
                node.id,
                node.words,
            )
        case 'sentence':
            return new Sentence(
                node.id,
                node.words,
            )
    }
}


class Link {
    constructor(id) {
        this.id = id;
    }
    handle(message) {
        switch (message) {
            case "childLinkOver":
                d3.select(`#${this.id}`)
                  .attr("stroke", "#61c079")
                  .attr("stroke-width", 4)
                break;

            case "parentLinkOver":
                d3.select(`#${this.id}`)
                  .attr("stroke", "#7185eb")
                  .attr("stroke-width", 4)
                break;

            default:
                d3.select(`#${this.id}`)
                  .attr("stroke", "#272f3f")
                  .attr("stroke-width", 2)
        }
    }
}

function buildLink(edge) {
    return new Link(
        `ln-${edge.source}-${edge.target}`
    );
}

function makeConnections(edge, comsNodes, comsLinks) {
    source = comsNodes[edge.source];
    target = comsNodes[edge.target];
    link = comsLinks[`ln-${edge.source}-${edge.target}`];

    // 'constructor' is aparently how to get the name of user-defined objects
    switch (source.constructor) { 
        case Sentence:
            // Sentence links
            source.children.push(target);
            source.childLinks.push(link);

            // Phrase links
            target.context = source;
            target.contextLink = link;
            break;
        case Phrase:
            // Phrase links
            source.definition = target;
            source.definitionLink = link;

            // Sentence links
            target.parent = source;
            target.parentLink = link;
            break;
    }
};


function buildComsSystem(graph) {
    let comsNodes = {};
    let comsLinks = {};
    graph.nodes.forEach((node) => comsNodes[node.id] = buildNode(node));
    graph.edges.forEach((edge) => {
        comsLinks[`ln-${edge.source}-${edge.target}`] = buildLink(edge)
    });
    graph.edges.forEach((edge) => makeConnections(edge, comsNodes, comsLinks));
    
    return comsNodes;
}
